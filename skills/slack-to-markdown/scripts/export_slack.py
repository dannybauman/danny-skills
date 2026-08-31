import os
import re
import sys
import argparse
import html
import csv
import io
import urllib.request
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

    # 3b. Channel refs <#C123|name> -> #name. Slack omits the label when the channel was
    # linked by ID, and there's no name to recover without an API call, so keep the ID
    text = re.sub(r'<#([A-Z0-9]+)\|([^>]*)>', lambda m: '#' + (m.group(2) or m.group(1)), text)
    text = re.sub(r'<#([A-Z0-9]+)>', r'#\1', text)

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

        # Slack only treats * and _ as emphasis at word boundaries. Without the
        # \w guards these eat underscores inside URLs, snake_case and :emoji_names:
        # Bold (*text* -> **text**)
        line = re.sub(r'(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])', r'**\1**', line)

        # Italic (_text_ -> *text*)
        line = re.sub(r'(?<![\w*])_([^_\s][^_]*)_(?![\w*])', r'*\1*', line)

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


def resolve_users(client, messages, user_map=None):
    """Collect all user IDs from message authors and body @-mentions (including expanded
    thread replies), then resolve to names.

    Pass an existing user_map to accumulate across calls. List mode resolves per row and the
    same people recur, so without this every row re-fetches them and burns the users.info
    rate limit -- and a 429 here is swallowed below, degrading names to raw IDs silently."""
    user_map = {} if user_map is None else user_map
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

    user_ids -= user_map.keys()
    if not user_ids:
        return user_map

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


def lookup_channel_name(client, channel_id, cache=None):
    """Channel ID -> name, falling back to the ID. Pass a cache dict to reuse across calls
    (List mode looks one up per row, and conversations.info is rate limited)."""
    if cache is not None and channel_id in cache:
        return cache[channel_id]
    name = channel_id
    try:
        name = client.conversations_info(channel=channel_id)["channel"]["name"]
    except SlackApiError:
        pass
    if cache is not None:
        cache[channel_id] = name
    return name


def render_message(msg, user_map, quoted=False, heading=False):
    """Render one message as markdown lines. Shared by every mode so a message exports the
    same way regardless of which mode fetched it.
      quoted  -> nested as a blockquote (thread replies)
      heading -> the `### Name [ts]` form used for a thread's parent
    """
    user = user_map.get(msg.get("user"), "Unknown User")
    dt = datetime.fromtimestamp(float(msg.get("ts", 0))).strftime('%Y-%m-%d %H:%M:%S')
    body = "\n\n".join(p for p in (
        format_slack_text(msg.get("text", ""), user_map),
        format_message_extras(msg, user_map),
    ) if p)

    if quoted:
        lines = [f"> **{user}** [{dt}]", "> " + body.replace("\n", "\n> ") + "\n"]
    elif heading:
        lines = [f"### {user} [{dt}]", f"{body}\n"]
    else:
        lines = [f"**{user}** [{dt}]", f"{body}\n"]

    reactions = msg.get("reactions")
    if reactions:
        lines.append("*Reactions: " + ", ".join(
            f":{r['name']}: x{r['count']}" for r in reactions) + "*\n")
    return lines


def write_output(md_lines, filename, args):
    """Write the assembled markdown to --output-dir (default <skill>/output)."""
    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser().resolve()
    else:
        output_dir = _skill_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    with open(output_path, "w") as f:
        f.write("\n".join(md_lines))
    print(f"[+] Successfully exported to: {output_path}")


def parse_list_url(url):
    """
    Parses a Slack List URL.

    Supported formats:
      - Whole list:    https://workspace.slack.com/lists/T12345678/F12345678
      - Single record: https://workspace.slack.com/lists/T12345678/F12345678?record_id=Rec0123
    Returns (list_file_id, record_id_or_None), or None if this isn't a list URL.
    """
    m = re.search(r'/lists/[A-Z0-9]+/([A-Z0-9]+)', url)
    if not m:
        return None
    rec = re.search(r'record_id=([A-Za-z0-9]+)', url)
    return m.group(1), (rec.group(1) if rec else None)


def fetch_list(client, token, list_id):
    """
    Returns (title, rows) for a Slack List, where rows is a list of dicts keyed by column name.

    Slack Lists are stored as files (mimetype application/vnd.slack-list) and the row data is
    NOT in files.info -- it comes from the `list_csv_download_url` that files.info hands back.
    That URL needs the same bearer token as the API, and only `files:read`, which is why this
    works without the `lists:read` scope that slackLists.* requires.
    """
    info = client.files_info(file=list_id)["file"]
    title = info.get("title") or list_id
    csv_url = info.get("list_csv_download_url")
    if not csv_url:
        raise ValueError(
            f"No CSV export available for list {list_id}. "
            "files.info returned no list_csv_download_url -- is this actually a List?"
        )
    req = urllib.request.Request(csv_url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(body)))
    return title, rows


def apply_filters(rows, filters):
    """Keeps rows where every `COLUMN=VALUE` filter matches (case-insensitive substring)."""
    for col, needle in filters:
        needle = needle.lower()
        matched = [r for r in rows if needle in (r.get(col) or "").lower()]
        if not matched:
            cols = ", ".join(rows[0].keys()) if rows else "(none)"
            raise ValueError(f"Filter {col}={needle!r} matched no rows. Columns: {cols}")
        rows = matched
    return rows


def fetch_permalink_message(client, url):
    """
    Fetches the message a Slack permalink points at.

    Returns (channel_id, [messages]) -- the whole thread when the permalink is part of one,
    a single-message list otherwise. A point read of one message is conversations_history
    with oldest==latest and inclusive=True.
    """
    channel_id, ts = parse_slack_url(url)
    if not ts:
        return channel_id, []
    if "thread_ts=" in url:
        resp = client.conversations_replies(channel=channel_id, ts=ts, limit=200)
        return channel_id, resp.get("messages", [])

    resp = client.conversations_history(
        channel=channel_id, oldest=ts, latest=ts, inclusive=True, limit=1
    )
    messages = resp.get("messages", [])
    # A permalink copied from a thread's PARENT carries no thread_ts -- Slack only adds that
    # param to links pointing at a reply. Without this check the parent exports on its own and
    # the replies are silently dropped
    if messages and messages[0].get("reply_count"):
        resp = client.conversations_replies(channel=channel_id, ts=ts, limit=200)
        return channel_id, resp.get("messages", [])
    return channel_id, messages


def export_list(client, token, url, list_id, record_id, args):
    """Exports a Slack List to Markdown, expanding each row's linked Slack message inline."""
    if record_id:
        # The CSV export carries no record IDs, so there is nothing to match a record_id
        # against. The slackLists.* methods that could resolve one need the `lists:read`
        # scope, which this CSV path deliberately avoids
        print(f"[!] record_id={record_id} can't be matched to a row -- the CSV export carries "
              "no record IDs.")
        print("[!] Exporting the whole list instead -- narrow it with --filter COLUMN=VALUE.")

    title, rows = fetch_list(client, token, list_id)
    print(f"[*] List mode: {title!r} ({len(rows)} rows)")

    if args.filter:
        filters = []
        for f in args.filter:
            if "=" not in f:
                raise ValueError(f"--filter needs COLUMN=VALUE, got {f!r}")
            col, val = f.split("=", 1)
            filters.append((col.strip(), val.strip()))
        rows = apply_filters(rows, filters)
        print(f"[*] {len(rows)} row(s) after filtering")

    md = [f"# {title}", f"- **Rows**: {len(rows)}",
          f"- **Exported At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
          f"- **Source**: [Slack List]({url})", "\n---\n"]

    # Shared across every row: the same people and channels recur, and both lookups are
    # rate limited, so a per-row cache is the difference between one call and one per row
    user_map, channel_cache = {}, {}

    for i, row in enumerate(rows, 1):
        # Any cell may hold the permalink; Slack's own column naming is user-defined, so find
        # the link by shape rather than by trusting a column name
        link = next((v for v in row.values() if v and "/archives/" in v), None)
        header = next((v for v in row.values() if v and "/archives/" not in v), f"Row {i}")

        messages, channel_id = [], None
        fetch_error = None
        if link:
            try:
                channel_id, messages = fetch_permalink_message(client, link)
            except (SlackApiError, ValueError) as e:
                fetch_error = e
            if messages:
                resolve_users(client, messages, user_map)

        # Row titles are raw Slack markup (the list stores the message preview verbatim), so
        # they need the same formatting pass as message bodies -- and that needs user_map,
        # which is why the fetch happens before the heading is written
        # Slack truncates the stored preview mid-string, which can cut a <url|label> in half
        # and leave markup the formatter has no closing bracket to match
        heading = re.sub(r'<[^>]*$', '', format_slack_text(header, user_map)).strip()
        # A CSV cell can carry newlines, which would break out of the `##` heading
        heading = " ".join(heading.split())
        md.append(f"## {i}. {heading[:160]}")
        for k, v in row.items():
            if v and "/archives/" not in v and v.strip() != header.strip():
                md.append(f"- **{k}**: {v}")
        if not link:
            md.append("")
            continue
        md.append(f"- **Link**: {link}")
        if fetch_error is not None:
            md.append(f"\n> Could not fetch message: {fetch_error}\n")
            continue
        if not messages:
            md.append("\n> Message not found (deleted, or the token can't see that channel)\n")
            continue
        md.append(f"- **Channel**: #{lookup_channel_name(client, channel_id, channel_cache)}\n")
        for j, msg in enumerate(messages):
            md.extend(render_message(msg, user_map, quoted=(j > 0)))

    filename = args.output or f"slack_list_{list_id}_{datetime.now().strftime('%Y-%m-%d')}.md"
    write_output(md, filename, args)


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
    parser.add_argument("--filter", action="append", metavar="COLUMN=VALUE",
                        help="List mode only: keep rows whose COLUMN contains VALUE "
                             "(case-insensitive). Repeatable; filters AND together.")
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
        # Slack Lists live at /lists/TEAM/FILE, not /archives/, and parse_slack_url rejects them
        list_target = parse_list_url(args.url)
        if list_target:
            export_list(client, token, args.url, list_target[0], list_target[1], args)
            return

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
        channel_name = lookup_channel_name(client, channel_id)

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

            md_content.extend(render_message(
                msg, user_map, heading=(mode == "thread" and i == 0)))

            if expand_threads and msg.get("_replies"):
                for reply in msg["_replies"]:
                    md_content.extend(render_message(reply, user_map, quoted=True))
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

        write_output(md_content, filename, args)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
