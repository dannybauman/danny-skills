// Concatenate src/*.js into one self-contained HTML page, with the mixed audio inlined as base64.
//   node tools/build.mjs        -> output/<name>.html   (run from the project root)
import { readFileSync, writeFileSync, readdirSync, existsSync, mkdirSync } from 'node:fs';
const VIDEO = JSON.parse(readFileSync('video.json', 'utf8'));
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const js = readdirSync('src').filter(f => f.endsWith('.js')).sort().map(f => `// ---- ${f}\n` + readFileSync(`src/${f}`, 'utf8')).join('\n');
const audioPath = ['audio/final_mix.m4a', 'audio/final_mix.mp3'].find(existsSync);
const audio = audioPath ? `data:${audioPath.endsWith('m4a') ? 'audio/mp4' : 'audio/mpeg'};base64,` + readFileSync(audioPath).toString('base64') : '';
const ar = VIDEO.width / VIDEO.height;
const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(VIDEO.title)}</title>
<style>
  html, body { margin: 0; height: 100%; background: #171513; overflow: hidden; }
  #stage { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: min(100vw, ${(ar * 100).toFixed(2)}vh); height: min(${(100 / ar).toFixed(2)}vw, 100vh); cursor: pointer; display: block; }
  body.render #stage { left: 0; top: 0; transform: none; width: ${VIDEO.width}px; height: ${VIDEO.height}px; cursor: default; }
</style>
</head>
<body>
<canvas id="stage" width="${VIDEO.width}" height="${VIDEO.height}" aria-label="${esc(VIDEO.description || VIDEO.title)}"></canvas>
<audio id="snd" preload="auto"${audio ? ` src="${audio}"` : ''}></audio>
<script>
'use strict';
const VIDEO = ${JSON.stringify(VIDEO)};
${js}
</script>
</body>
</html>
`;
mkdirSync('output', { recursive: true });
writeFileSync(`output/${VIDEO.name}.html`, html);
console.log(`built output/${VIDEO.name}.html  ${(html.length / 1e6).toFixed(2)} MB  audio: ${audioPath || 'none (silent build)'}`);
