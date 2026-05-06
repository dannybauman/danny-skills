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
    Parses a Slack URL to extract Channel ID and Thread Timestamp.
    Example URL: https://workspace.slack.com/archives/C12345678/p1700000000000000
    """
    # Regex to match archives/CHANNEL_ID/pTIMESTAMP
    match = re.search(r'archives/([A-Z0-9]+)/p(\d+)', url)
    if not match:
        raise ValueError("Invalid Slack URL format. Expected archives/CHANNEL_ID/pTIMESTAMP")

    channel_id = match.group(1)
    timestamp_str = match.group(2)

    # Slack timestamps in URLs are multiplied by 1,000,000 and have no dot
    # p1706891234123456 -> 1706891234.123456
    if len(timestamp_str) > 6:
        ts = f"{timestamp_str[:-6]}.{timestamp_str[-6:]}"
    else:
        ts = timestamp_str # Fallback

    return channel_id, ts

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

def main():
    parser = argparse.ArgumentParser(description="Export Slack conversation to Markdown")
    parser.add_argument("url", help="Slack message or thread URL")
    parser.add_argument("--output", help="Optional output filename")
    parser.add_argument("--output-dir", help="Optional output directory (default: <skill>/output)")
    parser.add_argument("--token", help="Slack API token (xoxp- or xoxb-)")
    args = parser.parse_args()

    token = args.token or os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("Error: Slack token not provided via --token or SLACK_BOT_TOKEN environment variable.")
        sys.exit(1)

    client = WebClient(token=token)
    user_map = {}

    try:
        channel_id, thread_ts = parse_slack_url(args.url)
        print(f"[*] Parsing URL: Channel={channel_id}, TS={thread_ts}")

        # Fetch conversation replies (this includes the parent message)
        print(f"[*] Fetching conversation history...")
        result = client.conversations_replies(channel=channel_id, ts=thread_ts)
        messages = result.get("messages", [])

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

        # Collect user IDs to resolve names — both message authors AND
        # any <@U_id> mentions inside message text. Without the body scan,
        # @-mentions in the rendered output stay as raw IDs.
        user_ids = set()
        mention_pattern = re.compile(r'<@([A-Z0-9]+)>')
        for msg in messages:
            if "user" in msg:
                user_ids.add(msg["user"])
            text = msg.get("text", "") or ""
            user_ids.update(mention_pattern.findall(text))

        print(f"[*] Resolving {len(user_ids)} users (authors + body @-mentions)...")
        for uid in user_ids:
            try:
                user_info = client.users_info(user=uid)
                profile = user_info["user"].get("profile", {})
                # display_name can be empty string for users who never set one;
                # fall back to real_name. The previous "@" + dn or rn precedence
                # silently produced "@" when dn was empty.
                name = profile.get("display_name") or user_info["user"].get("real_name") or uid
                user_map[uid] = f"@{name}"
            except SlackApiError:
                user_map[uid] = f"@{uid}"

        # Build Markdown
        md_content = []
        md_content.append(f"# Slack Conversation Export")
        md_content.append(f"- **Channel**: #{channel_name}")
        md_content.append(f"- **Exported At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md_content.append(f"- **Source**: [Slack Link]({args.url})")
        md_content.append("\n---\n")

        for i, msg in enumerate(messages):
            user = user_map.get(msg.get("user"), "Unknown User")
            ts = float(msg.get("ts", 0))
            dt = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            text = msg.get("text", "")
            formatted_text = format_slack_text(text, user_map)

            if i == 0:
                md_content.append(f"### {user} [{dt}]")
            else:
                md_content.append(f"**{user}** [{dt}]")

            md_content.append(f"{formatted_text}\n")

            # Sub-threads (rare in export_replies but good to note)
            if "reply_count" in msg and i == 0:
                md_content.append(f"\n*Thread contains {msg['reply_count']} replies:*\n")

        # Save output
        if args.output:
            filename = args.output
        else:
            filename = f"slack_export_{channel_id}_{thread_ts.replace('.', '')}.md"

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
