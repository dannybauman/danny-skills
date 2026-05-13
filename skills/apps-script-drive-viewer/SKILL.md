---
name: apps-script-drive-viewer
description: Build a Google Apps Script web app that reads data from Google Drive and serves HTML, restricted to a Google Workspace domain. Use when a team wants a click-to-view URL for confidential data without GitHub Pages or download-and-open friction. Triggers include "Apps Script web app", "Drive-backed tool", "domain-restricted viewer", "Workspace-only HTML", "convert this static HTML to read from Drive", or "internal team should click a URL and see this".
---

# Apps Script Drive Viewer

Build pattern for **Drive-backed, Workspace-domain-restricted HTML viewers** using Google Apps Script.

## CRITICAL: how to interact with the user

**Proceed call-and-response. One question at a time. Adapt to their experience level.**

Do NOT:
- Dump the architecture, walkthrough, or list of steps upfront
- Present multi-option menus or numbered checklists for them to pick from
- Run commands without confirming readiness
- Assume the user knows what clasp, Google Workspace, OAuth scopes, the CLI, markdown, or Drive sharing permissions are
- Quote big chunks of the README at them
- Say "I'll walk you through 8 steps" — just walk

Do:
- **Open with one sentence + one question.** No more than two short sentences before the first question. Example: *"Building a Drive-backed web tool your team will open at a URL — about 30 min if everything's ready. Have you set up something like this before, or is this new?"*
- **Identify the next blocking step at each turn** based on what's been established so far. Ask the most useful single question to unblock that step
- **Calibrate depth to their signals.** If they use jargon fluently (clasp, OAuth, HtmlService), trust their experience and ask shorter questions. If they pause on basic terms, explain briefly before asking
- **Run commands and verify, then move on.** Don't preview commands you're about to run unless they'd want a heads-up

## State to track (find the next unblocked step each turn)

At any moment, look at what's been established. The next question is about the next unmet item:

1. **Project identity** — name? local directory? (defaults exist; suggest if they're unsure)
2. **Prereqs**
   - Google Workspace account (not personal Gmail — needed for domain restriction)
   - Node.js installed
   - clasp installed (`npm install -g @google/clasp`)
   - clasp logged in (with Workspace account, not personal)
   - Apps Script API enabled at https://script.google.com/home/usersettings
3. **Data file**
   - Uploaded to Drive (DS confidential ops folder for DS use case, or wherever fits)
   - File ID known (from share URL)
4. **Existing tool source** (only if porting from existing HTML, which is the most common case)
   - Path to existing tool's `index.html` (or equivalent)
   - Name of the data file the existing tool loads (usually a `<script src="...">` line)
5. **Project scaffolded** — run `scripts/new-project.sh <name> <parent-dir>` from this skill
6. **Apps Script project created** — `clasp create --type webapp` in the new project dir
7. **Data file ID wired** — `DATA_FILE_ID` script property set in Project Settings
8. **HTML adapted** — existing tool's render code dropped into `Index.html`, `<script src="data.js">` line replaced with `<script><?!= dataContent ?></script>`
9. **Pushed** — `./deploy-helper.sh push`
10. **Deployed with domain restriction** — Apps Script editor → Deploy → Web app → "Execute as: Me", "Who has access: Anyone within {Workspace}"
11. **Tested as non-owner Workspace user** — teammate hits the URL, sees it work

At each turn: which of these is unmet AND unblocked? Ask about that. Just that.

## Light prompts for the most useful first questions

These are starting points. If the user has already given context that answers them, skip.

- *"Have you done this kind of setup before, or is this a first time with clasp + Apps Script?"*
- *"Do you have a Google Workspace account, or just a personal Gmail? (Domain restriction needs Workspace.)"*
- *"Is your data file already in Drive? If yes, drop the share URL or file ID and I'll pick it up from there."*
- *"Are you porting an existing HTML/JS tool, or starting from scratch?"* (If porting: ask for path. If fresh: starter has placeholder render to fill in.)

## When to run new-project.sh

Once you have:
- Project name
- Target parent directory

Run: `{SKILL_DIR}/scripts/new-project.sh <name> <parent-dir>`

Then continue with whatever's the next unblocked step.

## Adapting the HTML (the trickiest non-CLI step)

Most users hit this when porting an existing tool. The bulk of the existing HTML/CSS/JS usually works as-is. The only structural change is:

- Find the line that loads the data file (often `<script src="some-data.js"></script>`)
- Replace with `<script><?!= dataContent ?></script>`

If the existing tool uses CDN libraries (jQuery, Chart.js, etc.), see `references/htmlservice-csp-gotchas.md` — those need inlining because the IFRAME sandbox blocks external scripts.

Don't paste the whole existing index.html at the user — ask if you can read it from a path they provide, then make the edits directly in the new project's Index.html.

## When to load each reference

- `references/htmlservice-csp-gotchas.md` — when the existing HTML uses CDN scripts, external fonts, or third-party libraries
- `references/driveapp-read-patterns.md` — when wiring the data read step or troubleshooting Drive reads
- `references/data-format-tradeoffs.md` — when picking the data shape for a new viewer (skip if they're porting)
- `references/clasp-and-deployment.md` — when troubleshooting clasp errors or making the URL stable across redeploys
- `references/domain-restriction-and-auth.md` — when the user hits "you need permission" errors or has questions about who can access

## When to use this pattern

Good fits:
- Internal-team viewers (dashboards, recruiting matrix, ops snapshots, project trackers)
- Confidential data the team needs to see, external parties shouldn't
- Tools where Google Workspace domain auth is sufficient
- Data that changes more often than code

Bad fits:
- Public-facing tools
- High-traffic apps (Apps Script has daily quotas)
- Complex backends
- Real-time collaborative editing (Sheets is better)

## Bundled resources

- `scripts/new-project.sh` — creates a new project from the starter template
- `assets/starter-project/` — complete minimal project (Code.gs, Index.html, appsscript.json, .clasp.json, deploy-helper.sh, README.md, .gitignore)
- `references/` — depth on specific topics, loaded only when needed

## What "done" looks like

The user has:
- A new project directory under their chosen path
- A working clasp + Apps Script setup
- A data file in Drive with the file ID known
- A deployed web app URL that opens cleanly for teammates after Workspace login
- A README they can re-read when they come back to update later

If any of those is missing, the next question is about that.

## Deploy flow: auto-run what you can, ask for what's irreducibly manual

After files are written, **do NOT hand the user a list of paste-into-terminal commands.** You have a shell — use it. Run the CLI work yourself, narrating as you go. Only ask the user for things that genuinely require a human (browser sign-ins, editor UI clicks, visual verification).

### The auto-run-able things (do these via Bash, narrate in one short sentence each)

| Action | Command | When |
|---|---|---|
| Check Node installed | `node --version` | Always, first |
| Check npm installed | `npm --version` | If Node found |
| Check clasp installed | `which clasp` or `clasp --version` | Always |
| Install clasp if missing | `npm install -g @google/clasp` | If clasp not found. May prompt for sudo |
| Check clasp login state | `clasp login --status` | Always |
| Create Apps Script project | `cd <project-dir> && clasp create --type webapp --title "..."` | After login |
| Push local code | `clasp push` | After create |
| Deploy | `clasp deploy --description "Initial deploy"` | After Script Properties are set |
| Get URL | parse from clasp deploy output | After deploy |

For all of these: run via Bash, show abbreviated output (last 5-10 lines is plenty), confirm success, move to the next thing. Don't ask the user to do these.

### The genuinely-manual things (ask the user, one at a time)

1. **clasp login** (when not logged in) — `clasp login` opens a browser. User signs in. You wait for them to return
2. **Setting `DATA_FILE_ID` in Script Properties** — Apps Script editor UI, 5 clicks. After running `clasp open`, give them:
   > In the Apps Script editor (just opened):
   > 1. Click ⚙️ Project Settings (left sidebar)
   > 2. Scroll to Script Properties at the bottom
   > 3. Click "Add script property"
   > 4. Property: `DATA_FILE_ID`, Value: `<the file ID they gave you earlier>`
   > 5. Click Save script properties
   > Tell me when it's saved.
3. **First-run OAuth consent for Drive scope** — happens automatically when they first open the deployed URL. Tell them: "Open the URL — you'll see a Google permission prompt asking for Drive read access. Accept it. Then the matrix should render."
4. **Visual verification** — they open the URL, confirm the tool renders

### Cadence

After files are built, the **first message** is a consent-check + summary of who-does-what:

> Built. Want me to run the deploy for you? I'll install clasp if needed, create the Apps Script project, push the code, and deploy it. You'll do three things: sign into clasp when a browser opens, paste the data file ID into the Apps Script editor (one screen of clicks), and accept a Google permission prompt when you first open the URL. About 5-8 minutes total.

If they say go: proceed. Each subsequent message is **either** (a) "I just did X, here's the result, doing Y next" **or** (b) "Your turn — do X, tell me when done." Never both in the same message. Never multi-action.

### Auto-run rules

- **Always check before installing.** Don't run `npm install -g @google/clasp` if `which clasp` already finds it. Report what's already there
- **Surface failures, don't bury them.** If a command exits non-zero, paste the error to the user and ask how they want to proceed. Don't silently retry
- **Use the user's actual values.** Their data file ID, project name, target directory. Never use placeholders in a step you're presenting to them
- **No "and" or `&&` chains in a single message.** If two CLI commands need to happen, run them both via Bash internally, but narrate the second one when the first finishes

### Closing message after the URL works

When the user confirms the URL renders:

> Done. The URL is stable — share it with your team. They'll need to be signed into their @developmentseed.com account when they open it.
>
> Two things for later:
> - **Data updates**: edit `matrix-data.js` in Drive. The viewer reads fresh on each load (cached 10 min); add `?refresh=1` to bust the cache immediately.
> - **Code updates**: edit locally, `clasp push`, then in the Apps Script editor go to Deploy → Manage deployments → pencil icon → "New version" → Deploy. Keeps the URL stable. (Don't click "New deployment" — that makes a new URL.)
>
> Same flow lives in `README.md` in the project folder.

### Things to NOT do in the closing flow

- **No upfront "what's built" enumeration** of files. They exist, that's enough
- **No PR-description-style change logs** ("Code.gs:23 — doGet(e) reads DATA_FILE_ID...")
- **No hallucinated bug-fix narration** ("fixed dead code in the starter") unless you actually diffed against the current starter file
- **No previewing all N steps upfront.** "5 steps, here they are: 1, 2, 3, 4, 5" defeats the one-thing-at-a-time pattern. The user can ask "how many more steps?" if they want a count
- **No jargon-heavy bullets.** "DriveApp.getFileById via DATA_FILE_ID script property" is for the README, not for chat with a first-time user

### Fallback for environments without Bash access

If the skill is invoked in a context that can't run shell commands (web-only Claude, restricted permissions, etc.), fall back to the older paste-commands pattern: one command per turn, the user runs it, reports back. Even in this fallback, **never hand the user a numbered list of all commands at once.** One step per turn, every time.
