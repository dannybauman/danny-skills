---
name: slack-to-markdown
description: Extracts Slack conversations — single threads, channel message ranges, or "from this message to now" — from a URL and saves as formatted Markdown. Use when the user wants to archive, share, or summarize a Slack discussion. Supports --since/--until date filtering, --threads to expand replies inline, and --from-here to export a channel from a linked message onward.
---

# Slack-to-Markdown

This skill takes a Slack thread URL or channel URL and exports the conversation to a clean, readable Markdown file. Modes:

- **Thread mode**: Pass a thread URL (`archives/CHANNEL_ID/pTIMESTAMP`) to export a single thread with all replies
- **Channel mode**: Pass a channel URL (`archives/CHANNEL_ID`) to export messages from the channel, optionally filtered by date range with `--since` and `--until`. Add `--threads` to expand each message's thread replies inline (nested as blockquotes)
- **From-here mode**: Pass a *message* URL (`archives/CHANNEL_ID/pTIMESTAMP`) with `--from-here` to export the whole channel from that message to the latest, threads expanded. This is the "catch me up from this message onward" mode

## Prerequisites

1.  **Slack User Token**: You must use a **User Token** (`xoxp-`).
2.  **Environment Variable**: Set your token as `SLACK_BOT_TOKEN`.

> [!CAUTION]
> **Avoid Bot Tokens (`xoxb-`)**: While Slack supports Bot Tokens, they require you to manually invite the bot to every single channel you want to export from. **This skill is optimized for User Tokens** to provide a seamless experience.

- `channels:history` (Public Channels)
- `groups:history` (Private Channels/DMs)
- `users:read` (Resolving Usernames)

## Environment & Compatibility

> [!IMPORTANT]
> **Local-First Skill**: This skill is highly recommended for use with **Claude Agent** running on your local machine.
>
> **Claude.ai Web Interface**: If you upload this skill to the Claude website, it may fail with a "Network Restriction" error because the website's code execution sandbox does not allow connections to `slack.com`.

## Copy-Paste Fallback

If network access is restricted or you don't want to use a token:
1.  **Select All** (`Cmd+A`) in the Slack thread you want to archive.
2.  **Paste** the content directly into the chat with Claude.
3.  Instruct Claude: "Please format this raw Slack content into the standard Markdown format defined in the `slack-to-markdown` skill."

## Missing Token? (Claude's Instructions)

If you (Claude) detect that `SLACK_BOT_TOKEN` is not set:
1.  **Ask the User**: "I don't have a Slack token. Do you have one, or do you need help getting one?"
2.  **Guided Setup**: If they need help, point them to the **Getting a Slack Token** section below.
3.  **Accept and Save**: If they provide a token, offer to save it: "I can save this token to a local `.env` file in the skill directory so you don't have to provide it again. Should I do that?"
4.  **Save Command**: If they agree, run `echo "SLACK_BOT_TOKEN=xoxp-..." > .env` in the skill directory.

## Getting a Slack Token (Fastest Way)

The easiest way to get a token is to use a **Manifest**.

1.  Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App**.
2.  When the modal appears (showing **From scratch** and **From a manifest**), choose **From a manifest**.
3.  Select your workspace.
4.  Paste the following YAML into the **Enter app manifest below** box (replace the existing content):

```yaml
display_information:
  name: Claude Slack Exporter
oauth_config:
  scopes:
    user:
      - channels:history
      - groups:history
      - users:read
      - channels:read
```

5.  Click **Next** and then **Create**.
6.  In the left sidebar, click **Install App**, then click **Install to Workspace**.
7.  Click **Allow**.
8.  Copy the **User OAuth Token** (starts with `xoxp-`).
9.  Set it in your terminal: `export SLACK_BOT_TOKEN="xoxp-your-token-here"`

> [!TIP]
> **Why User Scopes?**
> We use the `user` scopes in the manifest so you can export conversations from any public or private channel you are already a member of, without needing to "invite" a bot.

## Usage

### 1. Identify the Slack URL
Copy the link to the message/thread or channel you want to export:
- Thread: `https://workspace.slack.com/archives/C12345678/p1700000000000000`
- Channel: `https://workspace.slack.com/archives/C12345678`

### 2. Run the Export
```bash
# Export a thread
./run.sh "https://workspace.slack.com/archives/C12345678/p1700000000000000"

# Export today's channel messages
./run.sh "https://workspace.slack.com/archives/C12345678" --since "2026-05-27"

# Export channel messages in a date range
./run.sh "https://workspace.slack.com/archives/C12345678" --since "2026-05-20" --until "2026-05-27"

# Export channel messages since a specific time
./run.sh "https://workspace.slack.com/archives/C12345678" --since "2026-05-27 09:00"

# Export a channel range with every thread expanded inline
./run.sh "https://workspace.slack.com/archives/C12345678" --since "2026-05-27" --threads

# "Catch me up from this message to now" — channel from a linked message onward, threads expanded
./run.sh "https://workspace.slack.com/archives/C12345678/p1700000000000000" --from-here

# Providing token directly
./run.sh "https://workspace.slack.com/archives/C12345678" --token xoxp-your-token
```

Optional arguments:
- `--output [filename]`: Specify a custom output filename.
- `--output-dir [path]`: Specify a custom output directory. Default is `output/` next to the skill. Use this to land files directly in a vault path like `~/Source/my-vault/sources/slack/`.
- `--since [DATE]`: Fetch messages after this date. Format: `YYYY-MM-DD` or `YYYY-MM-DD HH:MM`. Channel mode only.
- `--until [DATE]`: Fetch messages before this date. Same format. Channel mode only.
- `--limit [N]`: Max messages to fetch in channel mode (default: 200).
- `--threads`: In channel mode, expand each message's thread replies inline (nested as blockquotes). Off by default to keep exports lean.
- `--from-here`: Given a *message* URL (`.../pTIMESTAMP`), export the whole channel from that message to the latest instead of just that one thread. Implies `--threads` and includes the linked message itself.

### 3. Retrieve the Markdown
The file will be saved in the `output/` directory. Claude can then read this file to summarize it or perform further analysis.

## How it works
1.  **URL Parsing**: Extracts the Channel ID and optional Thread Timestamp from the URL.
2.  **API Fetching**: Uses `conversations.replies` for threads, `conversations.history` for channel messages (with pagination and date-range filtering). With `--threads`/`--from-here`, it also calls `conversations.replies` for each threaded message and nests the replies under their parent. `--from-here` sets the linked message's timestamp as an inclusive `oldest` bound so the linked message itself is included.
3.  **User Resolution**: Resolves both message authors and any `<@U_id>` mentions found inside message bodies, so the rendered output replaces IDs with names everywhere they appear.
4.  **Formatting**: Converts Slack's mrkdwn into standard Markdown. Channel mode skips join/leave system messages.
5.  **Non-text content**: Messages whose `text` is empty because they only carry a shared message (a pasted Slack permalink) or a file/image no longer export blank. The shared message's link, author, and quoted body are surfaced inline (prefixed `↪`), and file posts list their name and link (prefixed `📎`). Applies to both top-level messages and expanded thread replies.

## Tips & Lessons Learned

-   **User Tokens vs. Bot Tokens**: Always prefer **User Tokens (`xoxp-`)** for personal archival tools. Bot Tokens are too restrictive and annoying because they require manual invites to every channel.
-   **Silent Install Reassurance**: Installing a Slack App is a **silent action**. It does not notify the workspace or channels.
-   **Manifest Setup**: Using the App Manifest is 10s of times faster than manual configuration and reduces the risk of missing a required scope.
-   **Local Persistence**: Saving the token to `.env` (gitignored) is the best balance between security and convenience for local agent skills.

## Troubleshooting

-   **"Invalid Slack URL"**: Ensure you are copying the link directly from the message's "Copy link" option in Slack. It should contain `archives/C.../p...`.
-   **"No such channel"**: Verify you are a member of the channel. User tokens only work for channels you have access to.
-   **"Token Error"**: If your token expires or is revoked, just delete the `.env` file and generate a new one using the Manifest guide.

## Packaging for Claude

If you want to zip this skill for upload, use this command to keep it clean and within file limits (it excludes the bulky `.venv` and your private `.env`):

```bash
zip -r slack-to-markdown.zip slack-to-markdown/ -x "*/.venv/*" "*/output/*" "*/input/*" "*/.env" "*/__pycache__/*" "*/.DS_Store"
```
