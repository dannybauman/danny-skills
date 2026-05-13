---
name: apps-script-drive-viewer
description: Conversationally build a Google Apps Script web app that reads a data file from Google Drive and serves HTML, restricted to a Google Workspace domain. Auto-runs CLI commands via Bash. Use when a team wants a click-to-view URL for confidential Drive-hosted data with Workspace SSO gating, or when porting a static HTML tool to Drive-backed hosting. Triggers include "Apps Script web app", "Drive-backed tool", "domain-restricted viewer", "Workspace-only HTML", "convert this static HTML to read from Drive", or "internal team should click a URL and see this".
---

# Apps Script Drive Viewer

This is a conversational skill. Talk to the user one step at a time. Auto-run CLI commands via Bash. Ask the user only for browser sign-ins, Apps Script editor UI clicks, and visual verification.

## State checklist

Copy this checklist into your working notes for the conversation. Mark each item as it's done:

```
Build state:
- [ ] Project name + local directory chosen
- [ ] Existing tool path identified (if porting)
- [ ] Data file ID known (Drive)
- [ ] Workspace account confirmed (not Gmail)
- [ ] Project scaffolded via scripts/new-project.sh
- [ ] Index.html adapted (data-loading line swapped)
- [ ] Node + clasp installed
- [ ] clasp logged in
- [ ] Apps Script project created (clasp create)
- [ ] Code pushed (clasp push)
- [ ] DATA_FILE_ID set in Script Properties (user action)
- [ ] Deployed with domain restriction (user action via editor)
- [ ] URL verified by non-owner Workspace user (user action)
```

At every turn, find the first unchecked AND unblocked item. Ask the user ONE question about it, or run ONE command via Bash to handle it.

## First message after the skill triggers

Send EXACTLY this format (substituting context if user gave any):

> Building a Drive-backed web tool your team will open at a URL. Have you done this kind of setup before, or is this new?

One sentence. One question. Wait for their answer before anything else.

## Auto-run via Bash (do not ask the user to paste these)

You have a shell. Use it. Run these commands yourself when their checklist item is the next unblocked thing. Narrate each in ONE sentence.

| Item | Command |
|---|---|
| Check Node | `node --version` |
| Check clasp installed | `which clasp` |
| Install clasp | `npm install -g @google/clasp` |
| Check clasp login | `clasp login --status` |
| Scaffold project | `${CLAUDE_SKILL_DIR}/scripts/new-project.sh <name> <parent-dir>` |
| Create Apps Script project | `cd <project-dir> && clasp create --type webapp --title "<title>"` |
| Push code | `clasp push` |
| Open editor | `clasp open` |

## Ask the user only for these (one per message, ever)

1. **clasp login OAuth** when not logged in. Send EXACTLY this:

   > `clasp login` opens a browser tab now. Sign in with your @developmentseed.com account (not personal gmail — Workspace domain restriction only works with Workspace). Tell me when you're back.

2. **Setting DATA_FILE_ID in Script Properties** after `clasp open`. Send EXACTLY this template, substituting the user's actual file ID:

   > In the Apps Script editor (just opened):
   > 1. Click ⚙️ Project Settings (left sidebar)
   > 2. Scroll to Script Properties at the bottom
   > 3. Click "Add script property"
   > 4. Property: `DATA_FILE_ID`, Value: `<their actual file ID>`
   > 5. Click Save script properties
   >
   > Tell me when it's saved.

3. **Deploy via editor** after `clasp push`. Send EXACTLY this template:

   > In the editor:
   > 1. Click Deploy (top right) → New deployment
   > 2. Click the gear icon next to "Select type" → Web app
   > 3. Execute as: **Me**
   > 4. Who has access: **Anyone within Development Seed** (their Workspace)
   > 5. Click Deploy
   > 6. Accept the Drive OAuth permission when prompted
   > 7. Copy the Web app URL from the dialog and paste it here

4. **Visual verification.** Send EXACTLY this template, substituting the URL:

   > Open `<url>` in an incognito window. Sign in with your @developmentseed.com account. Accept the Drive permission prompt. Tell me what you see — the matrix should render.

## Final message after the URL works

Send EXACTLY this:

> Done. The URL is stable — share it with your team.
>
> Two workflows for later:
> - **Data updates:** edit the file in Drive. Viewer reads fresh on each load (cached 10 min). Append `?refresh=1` to bust the cache immediately.
> - **Code updates:** edit locally, `clasp push`, then in the Apps Script editor go to Deploy → Manage deployments → pencil icon → "New version" → Deploy. URL stays stable.
>
> Same flow lives in `README.md` in the project folder.

Nothing else. No "what's built" recap. No technical justifications.

## Self-check before sending each message

Run this check mentally before sending any message:

- ✓ ONE action OR one ask — never both in the same message
- ✓ Plain language; jargon only in parentheticals if at all
- ✓ Uses user's actual values inline (no `<placeholder>` syntax in user-facing text)
- ✓ Matches the literal templates above when they apply

If any of these fail, rewrite before sending.

## Adapting the HTML (when porting an existing tool)

Most builds involve porting. The change is one line:

1. Find the line in the existing HTML that loads the data file (usually `<script src="..."></script>`)
2. Replace with `<script><?!= dataContent ?></script>`

Apply this edit directly to the new project's `Index.html`. Do not paste the whole existing HTML at the user.

If the existing tool uses CDN libraries (jQuery, Chart.js, Mapbox), see `references/htmlservice-csp-gotchas.md` — those need inlining.

## References (load only when needed)

- `references/htmlservice-csp-gotchas.md` — adapting HTML with CDN scripts or external libraries
- `references/driveapp-read-patterns.md` — wiring or debugging Drive reads
- `references/data-format-tradeoffs.md` — picking the data shape (`.js` vs `.json` vs Sheet)
- `references/clasp-and-deployment.md` — troubleshooting clasp or URL stability
- `references/domain-restriction-and-auth.md` — troubleshooting access issues

## Bundled assets

- `scripts/new-project.sh` — creates a new project from the starter (one command)
- `assets/starter-project/` — Code.gs, Index.html, appsscript.json, .clasp.json, deploy-helper.sh, README.md, .gitignore

## Fallback for environments without Bash

If you cannot run shell commands (web-only Claude or restricted permissions), fall back to one-command-per-turn paste pattern: send one command to the user, wait, respond with the next. Never send a numbered list of all commands at once.
