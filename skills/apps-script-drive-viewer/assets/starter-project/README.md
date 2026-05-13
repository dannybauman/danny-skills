# Tool Name

This is a Google Apps Script web app that reads data from Google Drive and serves an interactive HTML view, gated by your Google Workspace domain.

## What's in this folder

| File | Purpose |
|---|---|
| `Code.gs` | Apps Script server code — reads Drive, serves HTML |
| `Index.html` | The page that gets served — drop your tool's HTML here |
| `appsscript.json` | Manifest (timezone, OAuth scopes, web app config) |
| `.clasp.json` | clasp config — filled in by Step 3 |
| `deploy-helper.sh` | Shortcut commands for push / redeploy / logs |
| `.gitignore` | node_modules, auth files, OS junk |
| `README.md` | This file |

## Prerequisites

- A Google Workspace account (not a personal Gmail — domain restriction needs Workspace)
- Node.js + npm installed
- ~30 minutes for first build

If you're missing Workspace access for the domain you want to restrict to, stop here — that's a prereq, not a step.

---

## Step 1: Install clasp (~2 min, one-time per machine)

```bash
npm install -g @google/clasp
clasp login
```

`clasp login` opens a browser tab. Sign in with your **Workspace account**, not a personal Gmail.

Then enable the Apps Script API for your account: open https://script.google.com/home/usersettings and toggle "Google Apps Script API" to ON.

**Verify:** `clasp login --status` should print your Workspace email.

---

## Step 2: Place your data file in Drive (~3 min)

Upload your data file (a `.js` exporting globals, a `.json`, a `.txt`, etc.) to a Drive folder where confidential data lives. For DS: the team's confidential ops folder.

Right-click the file → "Share" → make sure your own Workspace account has access (it usually does, since you uploaded it).

Get the file ID from the share URL:
```
https://drive.google.com/file/d/{FILE_ID}/view?usp=sharing
                              ^^^^^^^^^^
                              copy this
```

Save the file ID — you'll paste it in Step 4.

---

## Step 3: Create the Apps Script project (~2 min)

From this directory:

```bash
clasp create --type webapp --title "Tool Name"
```

If prompted "Choose a script type", pick "standalone". This creates a new Apps Script project in your Drive and writes its script ID into `.clasp.json`.

**Verify:** `cat .clasp.json` shows a real `scriptId` value (not the placeholder).

---

## Step 4: Wire the data file ID (~1 min)

Open the Apps Script project in the editor:

```bash
clasp open
```

A browser tab opens the Apps Script editor. Then:

1. Click ⚙️ **Project Settings** in the left sidebar
2. Scroll to **Script Properties** at the bottom
3. Click **Add script property**
4. Property: `DATA_FILE_ID`
5. Value: the file ID from Step 2
6. Click **Save script properties**

**Verify:** the property shows in the list.

---

## Step 5: Drop your HTML/JS into Index.html (varies)

`Index.html` is currently a minimal placeholder. Replace it with your tool's actual content.

If you have an **existing static HTML tool** (the most common case):

1. Open your existing `index.html` (or whatever it's called)
2. Copy everything between (and including) `<!DOCTYPE html>` and `</html>` into this project's `Index.html`, replacing the placeholder content
3. Find the line that loads your data file. Probably looks like:
   ```html
   <script src="data.js"></script>
   ```
   or similar.
4. Replace that line with:
   ```html
   <script>
     <?!= dataContent ?>
   </script>
   ```
   This is HtmlService template syntax — the data file's contents will get inlined here at render time.
5. Make sure your script that uses the data globals runs *after* this `<script>` block.

**The rest of your HTML/CSS/JS usually works as-is.** The IFRAME sandbox in `Code.gs` allows most things, including Google Fonts and inline scripts.

If your tool uses external CDN scripts (jQuery, Chart.js, Mapbox, etc.), see the skill's `references/htmlservice-csp-gotchas.md` — they're blocked by the sandbox and need to be inlined.

---

## Step 6: Push code to Apps Script (~1 min)

```bash
./deploy-helper.sh push
```

You should see: `└─ appsscript.json` `└─ Code.gs` `└─ Index.html` `Pushed 3 files.`

If you get an auth error, run `clasp login` again.

---

## Step 7: First deploy (~3 min)

Open the editor (`clasp open` if it's not still open), then in the Apps Script editor:

1. Click **Deploy** (top right) → **New deployment**
2. Click the gear icon next to "Select type" → **Web app**
3. Description: `Initial deploy`
4. Execute as: **Me (your-email)** ← keeps Drive reads using your permissions
5. Who has access: **Anyone within Development Seed** (or your Workspace domain)
6. Click **Deploy**

The first deploy triggers an **OAuth consent screen** — review and accept the Drive read permission.

Copy the **Web app URL** from the success dialog. That's the URL you'll share.

**Verify:** open the URL in your current tab. You should see your tool render.

---

## Step 8: Test as a non-owner Workspace user (~3 min)

Critical step — verify domain restriction works:

1. Have a teammate open the URL in their browser
2. They should see the tool after Workspace login, ~1 second

If they see **"You need permission"** error:
- Open the Apps Script editor → Deploy → Manage deployments → edit your deployment
- Change "Who has access" to your Workspace domain
- Click Deploy

If they see a **500 error** or broken page:
- Run `./deploy-helper.sh logs` to see the execution error
- Most common: the data file isn't readable by your account, or the file ID is wrong

If they see "switch accounts" prompt:
- Normal — they have multiple Google accounts in the browser. They pick their Workspace one.

---

## Step 9: Share the URL

Slack the URL to whoever needs to see it. They can bookmark it. The URL is stable as long as you use `redeploy` instead of `deploy` for future updates (see Step 10).

---

## Step 10: Future updates

### To update the tool code

```bash
# Edit Index.html or Code.gs locally
./deploy-helper.sh push                 # push code to Apps Script
./deploy-helper.sh redeploy "what changed"  # promote to production, URL stays stable
```

### To update the data

Just edit the file in Drive. The web app reads fresh on each request (with a 10-min cache). Visit `<your-url>?refresh=1` to force a cache clear immediately after editing.

### When something breaks

- Check `./deploy-helper.sh logs` for server-side errors
- Open browser dev tools on the deployed URL to check for CSP / JS errors
- See the skill's references for deeper troubleshooting

---

## Common gotchas

- **URL changed unexpectedly** → you ran `deploy` instead of `redeploy`. Use `redeploy` to keep the URL stable
- **Recipients see "You need permission"** → "Who has access" setting is wrong on the deployment
- **External libraries (jQuery, Chart.js) silently fail** → CSP sandbox blocks them. Inline the library code. See skill's CSP gotchas reference
- **Fonts look wrong** → Google Fonts work but font files may fail on first load. Set CSS fallback fonts
- **`console.log` doesn't appear in browser console** → It's in Apps Script's execution log. Use `./deploy-helper.sh logs`
