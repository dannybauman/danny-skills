/**
 * Apps Script web app — reads a data file from Drive, serves it inlined into Index.html.
 *
 * Setup before first deploy:
 *   1. Project Settings → Script Properties → add DATA_FILE_ID = <Drive file ID>
 *   2. Deploy as web app:
 *        Execute as: Me (script owner)
 *        Who has access: Anyone within <your Workspace>
 *   3. First run triggers OAuth consent for Drive read access
 *
 * Data file in Drive: any text file (.js, .json, .txt). Content gets injected
 * into the HTML template as a string.
 */

function doGet(e) {
  // Allow ?refresh=1 to clear the data cache (for use right after editing the Drive file)
  if (e && e.parameter && e.parameter.refresh === '1') {
    CacheService.getScriptCache().remove('data_file_content');
  }

  const dataContent = readDataFile_();
  const template = HtmlService.createTemplateFromFile('Index');
  template.dataContent = dataContent;
  return template
    .evaluate()
    .setSandboxMode(HtmlService.SandboxMode.IFRAME)
    .setTitle('Tool Name');  // pre-filled by new-project.sh
}

/**
 * Read the data file from Drive. Returns its content as a string.
 * Cached for 10 minutes to cut latency on hot reads.
 */
function readDataFile_() {
  const cache = CacheService.getScriptCache();
  const cached = cache.get('data_file_content');
  if (cached) return cached;

  try {
    const fileId = PropertiesService.getScriptProperties().getProperty('DATA_FILE_ID');
    if (!fileId) {
      throw new Error('DATA_FILE_ID script property not set. Add it in Project Settings.');
    }
    const file = DriveApp.getFileById(fileId);
    const content = file.getBlob().getDataAsString();
    cache.put('data_file_content', content, 600);  // 10 min TTL
    return content;
  } catch (e) {
    Logger.log('readDataFile_ failed: ' + e.message);
    return 'window.DATA_LOAD_ERROR = ' + JSON.stringify(e.message) + ';';
  }
}
