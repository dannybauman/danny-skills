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

## Closing output style (CRITICAL — most builds fail here)

When the file generation step is done and the user has to take over with manual steps (clasp create, deploy, etc.), the closing message MUST:

- Lead with ONE plain-language sentence describing what was built
- Give 4-6 **numbered** next steps, each ONE concrete action with the command if applicable
- Bake in the user's actual values (their file ID, project name, etc.) — not placeholders
- End with a "Done when [X]" success line + a "If stuck, [Y]" escape hatch
- Use plain language. **No technical jargon, line numbers, file diff narration, or PR-description style change logs.** First-time users don't know what "USER_DEPLOYING", "DriveApp.getFileById", "Index.html:1660", "HtmlService template", or "OAuth scopes" mean
- NEVER report "bugs fixed in the starter while adapting it" or suggest back-ports unless you've actually compared against the current starter file. Hallucinated bug-fix narration erodes trust

**Bad (what NOT to write):**
> Built. Project lives at X. Code.gs:23 — doGet(e) reads DATA_FILE_ID via DriveApp.getFileById, inlines into Index template (10-min cache, ?refresh=1 busts). Index.html:1660 — `<script src="...">` swapped for `<?!= dataContent ?>`. appsscript.json — executeAs: USER_DEPLOYING + access: DOMAIN is the auth boundary. One bug fixed in the starter while adapting...
> 
> Next step is yours: cd X && clasp create --type webapp --title "...", upload Y to Drive, paste file ID into Script Properties, deploy domain-restricted.

**Good (what to write):**
> Built. The Apps Script project is in `recruiting/nasa-staffing-mockup/apps-script/`. The matrix tool's data-loading line was swapped to read `matrix-data.js` from Drive at request time.
>
> Five steps from here to a live URL:
>
> 1. **Open a terminal in the project folder:** `cd recruiting/nasa-staffing-mockup/apps-script`
> 2. **Log in to clasp** (if you haven't): `clasp login` — pick your @developmentseed.com account in the browser
> 3. **Create the Apps Script project:** `clasp create --type webapp --title "NASA Staffing Matrix"` (pick "Standalone" if it asks). This writes `.clasp.json` automatically.
> 4. **Push the code:** `clasp push`
> 5. **Configure + deploy via the browser:** `clasp open` to open the editor, then:
>    - **Project Settings → Script Properties** → Add `DATA_FILE_ID` = `<the file ID you gave me earlier>`
>    - **Deploy → New deployment → Type: Web app**, **Execute as: Me**, **Who has access: Anyone within Development Seed** → Deploy
>    - Accept the OAuth Drive permission when prompted
>    - Copy the Web app URL from the success dialog
>
> **Done when:** opening that URL in an incognito window (signed into your @developmentseed.com account) shows the matrix.
>
> **If you get stuck:** the project's `README.md` has the same steps with verification at each one. Slack me with what error you're seeing.

The good version uses bold step titles, concrete commands with the user's actual values inlined, and reserves jargon for parentheticals only. The "Done when" line gives the user something to test against.

This output style is the difference between "the tool works" and "the tool works AND the user knows how to use it."
