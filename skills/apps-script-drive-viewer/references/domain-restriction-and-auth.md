# Domain restriction and auth

How Apps Script's Workspace-domain restriction works, what users actually see, and what to verify before sharing.

## How domain restriction works

Apps Script web apps have a built-in access setting: "Who has access." Options:

- **Only myself** — default; only the script owner can load the URL
- **Anyone within Development Seed** — only users signed into a `@developmentseed.com` (or whatever your Workspace domain is) Google account
- **Anyone with Google account** — any authenticated Google user (overly broad for most internal tools)
- **Anyone** — fully public, no auth (don't use this for confidential data)

For DS internal tools, the right setting is **"Anyone within Development Seed"**.

This is Google Workspace SSO-style auth — it just works for anyone signed into the right Workspace account, no separate signup or password.

## What recipients see on first load

1. They click the web app URL
2. If they're signed into a `@developmentseed.com` Google account in their browser: they go straight to the tool. ~1 second
3. If they're signed into a different Google account (e.g., personal Gmail): Google shows a "switch account" page asking them to select the Workspace account
4. If they're not signed in at all: standard Google login flow, then the tool loads
5. If they're not in the Workspace at all: they see "You need permission" error. The page tells them to contact the owner (the script owner)

The "switch accounts" step is the only friction worth knowing about. Recipients with multiple Google accounts in the same browser will occasionally hit this.

## Permission scopes the script requests

The first time the script *owner* runs anything (or the first deploy), Apps Script asks for OAuth permission to:

- Read files from Drive (`https://www.googleapis.com/auth/drive.readonly` or similar)
- Read Sheets (if SpreadsheetApp is used)
- Send email (only if MailApp is used — skip if not)

Recipients don't see this consent screen — it's the script owner's. Recipients just see the tool, post-Workspace-login.

If you change the script to use a new API, the owner has to re-authorize. Apps Script will prompt automatically when this happens.

## Verifying access works correctly

Before sharing the URL widely, do this 5-min sanity check:

1. **Test as owner.** Open the URL signed in as the script owner. Tool loads. Baseline.
2. **Test as another Workspace user.** Have a teammate hit the URL. Should work seamlessly after their Workspace login. **Critical test.**
3. **Test as a non-Workspace Google user.** Open in incognito, sign into a personal `@gmail.com`. Should see "You need permission" error. Confirms domain restriction is on
4. **Test as fully signed out.** Open in incognito, no login. Should redirect to Google sign-in. After sign-in, behavior matches steps 2 or 3 depending on which account

If step 3 lets a non-Workspace user in: domain restriction is misconfigured. Re-check the deployment access setting.

## Scope of "Anyone within Development Seed"

This means anyone with an active `@developmentseed.com` Google account at the time of access. That includes:

- All current DS team members
- Contractors with `@developmentseed.com` accounts (if any have them)
- Recently-departed team members until their account is deactivated (this is a real consideration — if someone leaves, their access should be revoked via Workspace admin, not the script's deployment settings)

It does NOT include:

- Personal Gmail accounts of DS team members
- Contractors with their own company's email
- External partners (NASA, WRI, ESA people)

For tighter control (specific Workspace group, not whole domain), Apps Script supports group-based restrictions via Workspace Admin, but the deployment UI doesn't expose this directly. Most internal tools don't need this layer.

## Execute as: User vs Owner

The deployment setting "Execute as" matters for sensitive operations:

- **User accessing the web app** — script runs with the viewer's permissions. Their Drive access, their Calendar, etc.
- **Me (script owner)** — script runs with the owner's permissions. The owner's Drive access, files only they can see

For Drive reads of a confidential ops file, use **"Me (script owner)"** — the owner has access to the file, viewers don't need their own access to it. The script reads on their behalf.

For tools that read the viewer's own data (e.g., "show me my own files"), use **"User accessing the web app"**.

For the DS staffing matrix: **"Me (script owner)"** — viewers shouldn't need direct Drive access to `matrix-data.js`, the script reads it for them.

## What happens when the script owner leaves DS

If the script owner's Workspace account is deactivated, the script breaks. Recipients hit errors.

Two mitigations:

1. **Owner the script with a Workspace service account or a long-lived ops account** (e.g., a shared `tools@developmentseed.com` if that exists). Less common but eliminates the bus-factor risk
2. **Transfer ownership before someone leaves.** Apps Script has "Change owner" in the editor. Run through this as part of off-boarding for anyone who owns critical scripts

For a quick-and-dirty internal tool, owner = the person who built it is fine. For a tool the team relies on, plan for ownership continuity.
