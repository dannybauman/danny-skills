import os
import re
import sys
import argparse
import html
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load .env from script dir or skill root
_script_dir = Path(__file__).resolve().parent
_skill_dir = _script_dir.parent
load_dotenv(_skill_dir / ".env")

def parse_slack_url(url):
    """
    Parses a Slack URL to extract Channel ID and optional Thread Timestamp.

    Supported formats:
      - Thread:  https://workspace.slack.com/archives/C12345678/p1700000000000000
      - Channel: https://workspace.slack.com/archives/C12345678
    Returns (channel_id, thread_ts_or_None).
    """
    thread_match = re.search(r'archives/([A-Z0-9]+)/p(\d+)', url)
    if thread_match:
        channel_id = thread_match.group(1)
        timestamp_str = thread_match.group(2)
        if len(timestamp_str) > 6:
            ts = f"{timestamp_str[:-6]}.{timestamp_str[-6:]}"
        else:
            ts = timestamp_str
        return channel_id, ts

    channel_match = re.search(r'archives/([A-Z0-9]+)', url)
    if channel_match:
        return channel_match.group(1), None

    raise ValueError("Invalid Slack URL format. Expected archives/CHANNEL_ID or archives/CHANNEL_ID/pTIMESTAMP")

def format_slack_text(text, user_map):
    """
    Replaces Slack user IDs with names and does advanced formatting.
    """
    if not text:
        return ""

    # 1. Unescape HTML entities (&amp; -> &, etc.)
    text = html.unescape(text)

    # 2. Replace user tags <@U12345>
    def replace_user(match):
        user_id = match.group(1)
        return user_map.get(user_id, f"@{user_id}")

    text = re.sub(r'<@([A-Z0-9]+)>', replace_user, text)

    # 3. Convert Slack links <URL|Label> -> [Label](URL)
    text = re.sub(r'<(https?://[^|>]+)\|([^>]+)>', r'[\2](\1)', text)
    # Convert bare Slack links <URL> -> URL
    text = re.sub(r'<(https?://[^>]+)>', r'\1', text)

    # 4. Standardize mentions
    text = text.replace('<!here>', '@here').replace('<!channel>', '@channel')

    # 5. Handle lists and formatting line by line
    lines = text.split('\n')
    formatted_lines = []
    in_list = False

    for i, line in enumerate(lines):
        line_stripped = line.lstrip()

        # Handle Slack bullet character •
        if line_stripped.startswith('\u2022'):
            # Add a blank line before starting a list
            if not in_list and i > 0:
                if formatted_lines and formatted_lines[-1].strip() != "":
                    formatted_lines.append("")
            in_list = True
            # Replace bullet and ensure space after it
            line = line.replace('\u2022', '-', 1)
            line = re.sub(r'^(\s*)-(\S)', r'\1- \2', line)
        else:
            in_list = False

        # Handle simple blockquotes
        if line.startswith('&gt;'):
            line = "> " + line[4:].lstrip()
        elif line.startswith('>'):
            line = "> " + line[1:].lstrip()

        # Bold (*text* -> **text**)
        line = re.sub(r'(?<!\*)\*([^\*]+)\*(?!\*)', r'**\1**', line)

        # Italic (_text_ -> *text*)
        line = re.sub(r'(?<!\*)_([^_]+)_(?!\*)', r'*\1*', line)

        formatted_lines.append(line)

    return "\n".join(formatted_lines)

def format_message_extras(msg, user_map):
    """Render content that lives OUTSIDE a message's `text` field, so messages carrying
    only that content don't export blank. Two common cases both leave `text` empty:
      - a shared message (someone pastes a Slack permalink, Slack attaches the referenced
        message as an `is_share` attachment with `from_url` + `text` + author)
      - a file/image post (content is in `files`, not `text`)
    Returns markdown (possibly empty)."""
    parts = []
    for att in msg.get("attachments") or []:
        from_url = att.get("from_url")
        att_text = att.get("text", "") or ""
        if att.get("is_share") or (from_url and att_text):
            header = "↪ Shared message"
            author = att.get("author_subname") or att.get("author_name")
            if author:
                header += f" from @{author}"
            if att.get("channel_name"):
                header += f" in #{att['channel_name']}"
            if from_url:
                header += f": {from_url}"
            parts.append(header)
            if att_text:
                parts.append("> " + format_slack_text(att_text, user_map).replace("\n", "\n> "))
        else:
            # Generic link unfurl (title + link, or a bare fallback)
            title = att.get("title")
            link = att.get("title_link") or att.get("original_url") or from_url
            if title and link:
                parts.append(f"↪ [{title}]({link})")
            elif link:
                parts.append(f"↪ {link}")
            elif att_text:
                parts.append("> " + format_slack_text(att_text, user_map).replace("\n", "\n> "))
    for f in msg.get("files") or []:
        name = f.get("name") or f.get("title") or "file"
        ftype = f.get("filetype")
        link = f.get("permalink") or f.get("url_private")
        label = f"📎 {name}" + (f" ({ftype})" if ftype else "")
        parts.append(f"{label}: {link}" if link else label)
    return "\n\n".join(parts)

def parse_date(value):
    """Parse a date or datetime string into a Unix timestamp."""
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).timestamp()
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Cannot parse date '{value}'. Use YYYY-MM-DD or 'YYYY-MM-DD HH:MM'."
    )


def fetch_channel_messages(client, channel_id, oldest=None, latest=None, limit=200, inclusive=False):
    """Fetch channel messages with pagination, optionally bounded by time.
    inclusive=True includes a message whose ts exactly equals `oldest`/`latest`
    (Slack's history bounds are exclusive by default, which would drop the linked message)."""
    all_messages = []
    cursor = None
    kwargs = {"channel": channel_id, "limit": min(limit, 200)}
    if oldest is not None:
        kwargs["oldest"] = str(oldest)
    if latest is not None:
        kwargs["latest"] = str(latest)
    if inclusive:
        kwargs["inclusive"] = True

    while True:
        if cursor:
            kwargs["cursor"] = cursor
        result = client.conversations_history(**kwargs)
        batch = result.get("messages", [])
        all_messages.extend(batch)
        if len(all_messages) >= limit:
            all_messages = all_messages[:limit]
            break
        cursor = result.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    all_messages.sort(key=lambda m: float(m.get("ts", 0)))
    return all_messages


def resolve_users(client, messages):
    """Collect all user IDs from message authors and body @-mentions (including expanded
    thread replies), then resolve to names."""
    user_map = {}
    user_ids = set()
    mention_pattern = re.compile(r'<@([A-Z0-9]+)>')

    def collect(msg):
        if "user" in msg:
            user_ids.add(msg["user"])
        user_ids.update(mention_pattern.findall(msg.get("text", "") or ""))
        for reply in msg.get("_replies", []) or []:
            collect(reply)

    for msg in messages:
        collect(msg)

    print(f"[*] Resolving {len(user_ids)} users (authors + body @-mentions)...")
    for uid in user_ids:
        try:
            user_info = client.users_info(user=uid)
            profile = user_info["user"].get("profile", {})
            # Prefer the REAL name over the display-name handle. A terse handle (e.g. initials
            # or a nickname) doesn't say who the person is, which leads to mis-attribution when
            # a reader or an LLM guesses from it. real_name is the reliable map from a Slack
            # user to the actual person. Keep the handle in parens only when it differs from the
            # real name, so mentions stay traceable back to Slack.
            real = profile.get("real_name") or user_info["user"].get("real_name")
            display = profile.get("display_name")
            if real and display and display.lower() != real.lower():
                name = f"{real} ({display})"
            else:
                name = real or display or uid
            user_map[uid] = f"@{name}"
        except SlackApiError:
            user_map[uid] = f"@{uid}"
    return user_map


def main():
    parser = argparse.ArgumentParser(description="Export Slack conversation to Markdown")
    parser.add_argument("url", help="Slack thread URL or channel URL")
    parser.add_argument("--output", help="Optional output filename")
    parser.add_argument("--output-dir", help="Optional output directory (default: <skill>/output)")
    parser.add_argument("--token", help="Slack API token (xoxp- or xoxb-)")
    parser.add_argument("--since", type=parse_date, metavar="DATE",
                        help="Fetch messages after this date (YYYY-MM-DD or 'YYYY-MM-DD HH:MM')")
    parser.add_argument("--until", type=parse_date, metavar="DATE",
                        help="Fetch messages before this date (YYYY-MM-DD or 'YYYY-MM-DD HH:MM')")
    parser.add_argument("--limit", type=int, default=200,
                        help="Max messages to fetch in channel mode (default: 200)")
    parser.add_argument("--threads", action="store_true",
                        help="In channel mode, expand each message's thread replies inline")
    parser.add_argument("--from-here", action="store_true",
                        help="Given a message URL (/pTIMESTAMP), export the whole channel from that "
                             "message to latest (implies channel mode + --threads)")
    args = parser.parse_args()

    token = args.token or os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("Error: Slack token not provided via --token or SLACK_BOT_TOKEN environment variable.")
        sys.exit(1)

    client = WebClient(token=token)

    try:
        channel_id, thread_ts = parse_slack_url(args.url)

        # --from-here turns a message URL into "channel from this message to latest",
        # expanding every thread along the way. Useful for "catch me up from here onward".
        expand_threads = args.threads
        if thread_ts and args.from_here:
            oldest = float(thread_ts)
            since_label = datetime.fromtimestamp(oldest).strftime('%Y-%m-%d %H:%M')
            until_label = datetime.fromtimestamp(args.until).strftime('%Y-%m-%d %H:%M') if args.until else "now"
            print(f"[*] Channel-from-here mode: Channel={channel_id}, from {since_label} (the linked message) to {until_label}")
            print(f"[*] Fetching channel messages...")
            messages = fetch_channel_messages(
                client, channel_id, oldest=oldest, latest=args.until,
                limit=args.limit, inclusive=True,
            )
            mode = "channel"
            expand_threads = True
        elif thread_ts:
            # Thread mode (existing behavior)
            print(f"[*] Thread mode: Channel={channel_id}, TS={thread_ts}")
            print(f"[*] Fetching conversation replies...")
            result = client.conversations_replies(channel=channel_id, ts=thread_ts)
            messages = result.get("messages", [])
            mode = "thread"
            since_label = until_label = None
        else:
            # Channel mode
            since_label = datetime.fromtimestamp(args.since).strftime('%Y-%m-%d %H:%M') if args.since else "beginning"
            until_label = datetime.fromtimestamp(args.until).strftime('%Y-%m-%d %H:%M') if args.until else "now"
            print(f"[*] Channel mode: Channel={channel_id}, since={since_label}, until={until_label}")
            print(f"[*] Fetching channel messages...")
            messages = fetch_channel_messages(
                client, channel_id,
                oldest=args.since, latest=args.until,
                limit=args.limit,
            )
            mode = "channel"

        # Expand thread replies in channel mode when requested (--threads or --from-here)
        if mode == "channel" and expand_threads and messages:
            n_threads = sum(1 for m in messages if m.get("reply_count") and m.get("thread_ts") == m.get("ts"))
            if n_threads:
                print(f"[*] Expanding {n_threads} thread(s)...")
            for m in messages:
                if m.get("reply_count") and m.get("thread_ts") == m.get("ts"):
                    try:
                        rr = client.conversations_replies(channel=channel_id, ts=m["ts"])
                        m["_replies"] = rr.get("messages", [])[1:]  # skip the parent (already included)
                    except SlackApiError:
                        m["_replies"] = []

        if not messages:
            print("No messages found.")
            return

        # Fetch channel info for header
        channel_name = channel_id
        try:
            info = client.conversations_info(channel=channel_id)
            channel_name = info["channel"]["name"]
        except SlackApiError:
            pass

        user_map = resolve_users(client, messages)

        # Build Markdown
        md_content = []
        if mode == "thread":
            md_content.append(f"# Slack Conversation Export")
        else:
            md_content.append(f"# #{channel_name} — Channel Messages")
        md_content.append(f"- **Channel**: #{channel_name}")
        if mode == "channel":
            md_content.append(f"- **Range**: {since_label} to {until_label}")
            md_content.append(f"- **Messages**: {len(messages)}")
        md_content.append(f"- **Exported At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md_content.append(f"- **Source**: [Slack Link]({args.url})")
        md_content.append("\n---\n")

        for i, msg in enumerate(messages):
            # Skip channel_join/channel_leave subtypes in channel mode
            subtype = msg.get("subtype")
            if mode == "channel" and subtype in ("channel_join", "channel_leave"):
                continue

            user = user_map.get(msg.get("user"), "Unknown User")
            ts = float(msg.get("ts", 0))
            dt = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            text = msg.get("text", "")
            formatted_text = format_slack_text(text, user_map)
            extras = format_message_extras(msg, user_map)
            body = "\n\n".join(p for p in (formatted_text, extras) if p)

            if mode == "thread" and i == 0:
                md_content.append(f"### {user} [{dt}]")
            else:
                md_content.append(f"**{user}** [{dt}]")

            md_content.append(f"{body}\n")

            if expand_threads and msg.get("_replies"):
                for reply in msg["_replies"]:
                    r_user = user_map.get(reply.get("user"), "Unknown User")
                    r_dt = datetime.fromtimestamp(float(reply.get("ts", 0))).strftime('%Y-%m-%d %H:%M:%S')
                    r_text = format_slack_text(reply.get("text", ""), user_map)
                    r_extras = format_message_extras(reply, user_map)
                    r_body = "\n\n".join(p for p in (r_text, r_extras) if p)
                    md_content.append(f"> **{r_user}** [{r_dt}]")
                    md_content.append("> " + r_body.replace("\n", "\n> ") + "\n")
            elif "reply_count" in msg:
                md_content.append(f"*Thread: {msg['reply_count']} replies*\n")

        # Save output
        if args.output:
            filename = args.output
        else:
            if mode == "thread":
                filename = f"slack_export_{channel_id}_{thread_ts.replace('.', '')}.md"
            else:
                date_suffix = datetime.now().strftime('%Y-%m-%d')
                filename = f"slack_{channel_name}_{date_suffix}.md"

        if args.output_dir:
            output_dir = Path(args.output_dir).expanduser().resolve()
        else:
            output_dir = _skill_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename

        with open(output_path, "w") as f:
            f.write("\n".join(md_content))

        print(f"[+] Successfully exported to: {output_path}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
