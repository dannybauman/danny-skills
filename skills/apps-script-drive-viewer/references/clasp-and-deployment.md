# clasp CLI and deployment

`clasp` is Google's CLI for Apps Script. It bridges local files (Git-tracked) with the Apps Script project (cloud). Without clasp, you're editing in the Apps Script web editor with no real version control. With clasp, you write code locally, push to deploy.

## One-time setup

```bash
npm install -g @google/clasp
clasp login
```

`clasp login` opens a browser tab for Google OAuth. Sign in with the **Workspace account** that should own the script (not personal Gmail). The OAuth scopes are stored in `~/.clasprc.json`.

Make sure the Apps Script API is enabled for your Google account: visit `https://script.google.com/home/usersettings` and toggle Apps Script API on.

## Create a new Apps Script project

From a directory that will contain your local code:

```bash
clasp create --type webapp --title "Your Tool Name"
```

This creates a new Apps Script project in your Drive and writes a `.clasp.json` file locally with the project's script ID. The `--type webapp` flag sets it up for HTML serving.

Alternatively, if you've already created the project in the Apps Script editor:

```bash
clasp clone <scriptId>
```

The script ID is in the editor URL: `https://script.google.com/d/<SCRIPT_ID>/edit`.

## Push local code to Apps Script

```bash
clasp push
```

Syncs all `.gs` and `.html` files from the current directory to the Apps Script project. Will overwrite cloud files with local ones. Run after every code change.

`clasp push --watch` runs continuously and auto-pushes on file save.

## Pull cloud changes back to local

```bash
clasp pull
```

If someone edited via the web editor, pull to get those changes locally. Useful for resolving "I edited in both places" situations.

## Deploy as a web app

First deployment:

```bash
clasp deploy --description "Initial deploy"
```

This creates a versioned deployment with a URL like:

```
https://script.google.com/macros/s/<DEPLOYMENT_ID>/exec
```

**The deployment ID is what makes the URL stable.** Each new deployment gets a new ID and a new URL — recipients would need to re-bookmark.

To keep the URL stable across code changes:

1. Open the Apps Script editor for your project
2. Click "Deploy" → "Manage deployments"
3. Find the existing web app deployment, click the pencil icon
4. Change "Version" to "New version"
5. Click "Deploy"

The URL stays the same. The deployment serves the new code.

Or via clasp:

```bash
clasp deployments       # list existing deployments, get the deployment ID
clasp redeploy <deploymentId> --description "Updated version"
```

## Domain-restrict the web app

This is the critical step. By default, a new web app is "Only myself" — recipients get a permission error.

In Apps Script editor → Deploy → Manage deployments → edit your deployment:

- **Execute as:** "User accessing the web app" (so reads happen with their permissions, not yours)
- **Who has access:** "Anyone within Development Seed" (your Workspace domain)

Hit "Deploy" again to save. Domain restriction now in effect.

Verify: open the URL in an incognito window. Should redirect to Google login, then to the tool after Workspace auth.

## .clasp.json structure

```json
{
  "scriptId": "1AbCdEfG...",
  "rootDir": "."
}
```

Commit this to Git so anyone with the repo can `clasp push` (after their own `clasp login` and verifying they have access to the script project).

## Files that clasp pushes/pulls

By default, clasp syncs all `.gs` and `.html` files in `rootDir`. It also handles `appsscript.json` (the manifest).

`.gs` files are Apps Script's name for JavaScript files (server-side code).

## Useful flags

- `clasp open` — opens the script in the Apps Script editor (handy for debugging via the editor's UI)
- `clasp logs` — shows recent execution logs (Logger.log output)
- `clasp run <functionName>` — runs a server-side function from the CLI (useful for one-off tasks)
- `clasp version "description"` — creates a numbered version snapshot you can revert to

## Common gotchas

1. **`clasp push` overwrites cloud changes.** If you edited in the web editor and pushed locally without pulling, you lose the web edits. Habit: pull before edit, push after edit
2. **Apps Script API must be enabled.** Visit `https://script.google.com/home/usersettings` once
3. **Workspace account vs personal account.** clasp uses whoever you logged in as. Make sure it's the Workspace account
4. **`.clasp.json` is local-only** for sensitive script IDs if needed — gitignore it if the script ID is something you don't want public, or commit it if everyone with repo access should also have script access
