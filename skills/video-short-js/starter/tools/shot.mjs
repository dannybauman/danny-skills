// Look at frames while authoring. Several times make one labelled contact sheet.
//   node tools/shot.mjs <out.png> <scale> [cam=x,y,z] <t1> [t2 ...]
// Small sheets are cheap to look at: 0.25-0.33 for story and composition, 0.5 for one shot's detail.
import { chromium } from 'playwright-core';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
const VIDEO = JSON.parse(readFileSync('video.json', 'utf8'));
let [out, scale, ...times] = process.argv.slice(2);
let cam = null; if (times[0] && times[0].startsWith('cam=')) { const [x, y, z] = times.shift().slice(4).split(',').map(Number); cam = { x, y, z }; }
const browser = await chromium.launch({ channel: process.env.SHOT_CHANNEL || undefined, headless: true, args: ['--force-color-profile=srgb', '--force-device-scale-factor=1'] });
const page = await browser.newPage({ viewport: { width: VIDEO.width, height: VIDEO.height } });
page.on('console', m => console.log('[page]', m.text())); page.on('pageerror', e => console.log('[error]', e.message));
await page.goto('file://' + resolve(`output/${VIDEO.name}.html`) + '?render=1');
await page.evaluate(() => window.__ready);
if (cam) await page.evaluate(c => { window.__cam = c; }, cam);      // a scene may honour window.__cam as a debug camera
const data = await page.evaluate(([times, scale]) => {
  const src = document.getElementById('stage'), n = times.length, cols = n > 1 ? Math.ceil(Math.sqrt(n)) : 1, rows = Math.ceil(n / cols), w = Math.round(src.width * scale), h = Math.round(src.height * scale);
  const c = document.createElement('canvas'); c.width = w * cols; c.height = h * rows; const x = c.getContext('2d'); x.imageSmoothingQuality = 'high';
  const t0 = performance.now();
  times.forEach((t, i) => {
    window.__renderAt(t); x.drawImage(src, (i % cols) * w, Math.floor(i / cols) * h, w, h);
    if (n > 1) { x.fillStyle = 'rgba(0,0,0,.6)'; x.fillRect((i % cols) * w, Math.floor(i / cols) * h, 74, 24); x.fillStyle = '#fff'; x.font = '16px sans-serif'; x.fillText(t.toFixed(2), (i % cols) * w + 6, Math.floor(i / cols) * h + 17); }
  });
  console.log('ms/frame ' + ((performance.now() - t0) / n).toFixed(1) + '  (keep this well under 16 for smooth live playback)');
  return c.toDataURL('image/png');
}, [times.map(Number), Number(scale)]);
writeFileSync(out, Buffer.from(data.split(',')[1], 'base64'));
await browser.close();
