---
name: apps-script-drive-viewer
description: Build a Google Apps Script web app that reads data from Google Drive and serves HTML, restricted to a Google Workspace domain. Use when a team wants a click-to-view URL for confidential data without GitHub Pages or download-and-open friction. Triggers include "Apps Script web app", "Drive-backed tool", "domain-restricted viewer", "Workspace-only HTML", "convert this static HTML to read from Drive", or "internal team should click a URL and see this".
---

# Apps Script Drive Viewer

Build pattern for **Drive-backed, Workspace-domain-restricted HTML viewers** using Google Apps Script.

The architecture in one breath: **tool code lives in git, data lives in Drive, Apps Script reads Drive and serves HTML, URL is gated by Google Workspace domain.**

## How to use this skill

The skill ships a `new-project.sh` script that creates a working starter project with one command. When this skill triggers, do this:

1. **Run `scripts/new-project.sh <project-name> <target-parent-dir>`**
   - Creates a new project directory with all starter files
   - Pre-fills the project name in `Code.gs`
   - Makes scripts executable

2. **Point the user to the new project's `README.md`**
   - The README is the human-facing walkthrough — installation, Drive setup, deploy, test
   - Every step has a concrete command and a "you should see X" check
   - About 30 minutes from copy to live URL on the first build

3. **Help them adapt `Index.html`** if they're porting an existing static HTML tool
   - Replace their `<script src="data.js"></script>` line with `<script><?!= dataContent ?></script>`
   - The rest of their code (globals, render functions) usually works as-is
   - Use `references/htmlservice-csp-gotchas.md` if their HTML uses CDN scripts or external libraries

4. **Help debug deploy issues**
   - Use `references/clasp-and-deployment.md` for clasp command errors and URL stability
   - Use `references/domain-restriction-and-auth.md` for "you need permission" errors
   - Use `references/driveapp-read-patterns.md` for data read errors

## When to use this pattern

Good fits:
- Internal-team viewers (dashboards, recruiting matrix, ops snapshots, project trackers)
- Confidential data the team needs to see, external parties shouldn't
- Tools where Google Workspace domain auth is sufficient
- Data that changes more often than code

Bad fits:
- Public-facing tools (use real hosting)
- High-traffic apps (Apps Script has daily quotas)
- Complex backends (Apps Script is for view + light glue)
- Real-time collaborative editing (Sheets is better)

## Bundled resources

- `scripts/new-project.sh` — creates a new project from the starter template
- `assets/starter-project/` — complete minimal project (Code.gs + Index.html + appsscript.json + .clasp.json + deploy-helper.sh + README.md + .gitignore)
- `references/` — depth on specific topics, loaded only when needed:
  - `htmlservice-csp-gotchas.md` — CSP sandbox limits, IFRAME mode setup
  - `driveapp-read-patterns.md` — file reads, caching, error handling
  - `data-format-tradeoffs.md` — `.js` vs `.json` vs Google Sheet
  - `clasp-and-deployment.md` — clasp CLI, stable-URL vs new-deploy
  - `domain-restriction-and-auth.md` — Workspace auth, scopes, execute-as

## What "good" looks like at the end

The user has:
- A new project directory under their chosen path
- A working clasp + Apps Script setup
- A data file in Drive with a known file ID
- A deployed web app URL that opens cleanly for teammates after Workspace login
- A README they can re-read when they come back to update later

If any of those is missing, walk through the project's README again at the step that's broken.

## Pattern reuse

This skill is designed for ongoing reuse. Different DS tools (or any team's tools) can each be a separate Apps Script project built with this same pattern. The starter is intentionally generic — drop in your own HTML and data.

When a new use case lands, treat the existing build as proof the skill works; the new build just runs `new-project.sh` again with a different name.
