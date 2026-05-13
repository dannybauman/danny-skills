# DriveApp read patterns

Apps Script's `DriveApp` API reads files the script's owner has access to. This file shows the common patterns and what to use when.

## Get the Drive file ID

The file ID is in the share URL:

```
https://drive.google.com/file/d/{FILE_ID}/view?usp=sharing
                              ^^^^^^^^^
                              this part
```

Or for Google Docs/Sheets:

```
https://docs.google.com/spreadsheets/d/{FILE_ID}/edit
                                      ^^^^^^^^^
```

Save the file ID as a Script Property (not hardcoded) so it can be changed without editing code:

```javascript
// One-time setup: Apps Script editor → Project Settings → Script Properties → Add
// Key: DATA_FILE_ID
// Value: <the file ID from Drive URL>

const FILE_ID = PropertiesService.getScriptProperties().getProperty('DATA_FILE_ID');
```

## Pattern 1: Read a text file (JSON, JS, CSV, anything text-shaped)

For files that are plain text (matrix-data.js, config.json, etc.):

```javascript
function readDataFile() {
  const fileId = PropertiesService.getScriptProperties().getProperty('DATA_FILE_ID');
  const file = DriveApp.getFileById(fileId);
  return file.getBlob().getDataAsString();  // returns the file content as a string
}
```

This works for any text file under ~50MB.

## Pattern 2: Inline file content into HTML template

The most common pattern for a viewer: read the data file, inject its content into the HTML template before serving.

`Code.gs`:

```javascript
function doGet() {
  const dataContent = readDataFile();  // string of matrix-data.js content
  const template = HtmlService.createTemplateFromFile('Index');
  template.dataContent = dataContent;   // makes it available as <?= dataContent ?> in the template
  return template
    .evaluate()
    .setSandboxMode(HtmlService.SandboxMode.IFRAME)
    .setTitle('Tool Name');
}
```

`Index.html`:

```html
<!DOCTYPE html>
<html>
<head>...</head>
<body>
  <div id="root"></div>
  <script>
    <?!= dataContent ?>
    // ... rest of your tool's JS that uses the data
  </script>
</body>
</html>
```

The `<?!= ... ?>` syntax in HtmlService templates outputs the content without HTML-escaping (good for JS content). Use `<?= ... ?>` if you need HTML-escaping (good for user-facing strings to prevent XSS).

## Pattern 3: Read a Google Sheet as structured data

For Sheets as the data source:

```javascript
function readSheetData() {
  const sheetId = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  const ss = SpreadsheetApp.openById(sheetId);
  const sheet = ss.getSheetByName('Candidates');
  const data = sheet.getDataRange().getValues();  // 2D array, first row = headers
  return data;
}
```

Convert to objects keyed by header row:

```javascript
function readSheetAsObjects(sheetName) {
  const sheetId = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  const sheet = SpreadsheetApp.openById(sheetId).getSheetByName(sheetName);
  const rows = sheet.getDataRange().getValues();
  const headers = rows.shift();
  return rows.map(row => Object.fromEntries(headers.map((h, i) => [h, row[i]])));
}
```

## Pattern 4: Cache reads when the data doesn't change frequently

For data that updates every few days, caching cuts request latency from ~500ms to <50ms:

```javascript
function readDataFileCached() {
  const cache = CacheService.getScriptCache();
  const cached = cache.get('data_file_content');
  if (cached) return cached;

  const content = readDataFile();
  cache.put('data_file_content', content, 600);  // 10 min TTL
  return content;
}
```

Trade-off: edits to the Drive file won't show up until the cache expires. For weekly-edit cadence with daily-viewer pattern, 10-min cache is fine. For real-time-edit needs, skip caching.

## Pattern 5: Handle file-not-found gracefully

```javascript
function readDataFileSafe() {
  try {
    const fileId = PropertiesService.getScriptProperties().getProperty('DATA_FILE_ID');
    if (!fileId) throw new Error('DATA_FILE_ID script property not set');
    const file = DriveApp.getFileById(fileId);
    return file.getBlob().getDataAsString();
  } catch (e) {
    Logger.log('Failed to read data file: ' + e.message);
    return 'window.DATA_LOAD_ERROR = ' + JSON.stringify(e.message) + ';';
  }
}
```

In the HTML, check for `window.DATA_LOAD_ERROR` and show a friendly error message instead of a broken page.

## Permissions to know

- DriveApp requires the `https://www.googleapis.com/auth/drive` scope (or readonly variant). First deploy will prompt the owner to authorize
- The script reads files **as the owner** ("Execute as: User accessing the web app" doesn't change this for DriveApp calls — DriveApp always reads as the script user, which is the owner for a deployed web app). So the data file must be readable by the script owner's account
- If you want the data file to be readable only to a specific group, give the script owner's account access to the file (typically the same person, but worth knowing)

## Performance notes

- `DriveApp.getFileById` + `getBlob().getDataAsString()` for a ~50KB file: ~200-400ms cold, faster warm
- Apps Script cold-start adds 1-3 seconds on the first request after idle
- Sheets reads scale with size — `getDataRange().getValues()` for 1000 rows × 10 cols is fast (~200ms), 10000+ rows starts to feel slow
- Use `CacheService` for hot reads; use Properties for tiny config
