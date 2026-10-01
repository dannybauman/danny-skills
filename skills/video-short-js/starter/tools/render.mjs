#!/usr/bin/env node
// Renders a deterministic canvas page (window.__ready / __renderAt(t) / __DURATION / __FPS) to MP4, PNG or a contact sheet.
// Local only: playwright-core + the system ffmpeg, no network.
import { chromium } from 'playwright-core';
import { spawn } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { cpus } from 'node:os';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';

const VIDEO = JSON.parse(readFileSync('video.json', 'utf8'));      // run from the project root
const { values: o } = parseArgs({ options: {
  html: { type: 'string', default: `output/${VIDEO.name}.html` },
  audio: { type: 'string' }, 'no-audio': { type: 'boolean' },
  out: { type: 'string' }, from: { type: 'string' }, to: { type: 'string' },
  fps: { type: 'string' }, scale: { type: 'string', default: '1' },
  still: { type: 'string' }, sheet: { type: 'string' }, thumb: { type: 'string', default: '480' },
  workers: { type: 'string', default: String(Math.max(1, Math.min(4, cpus().length - 2))) },   // each worker is a browser: fewer on a busy machine
  crf: { type: 'string', default: '15' }, preset: { type: 'string', default: 'slow' },
} });
const abs = (p) => resolve(process.cwd(), p);
const htmlPath = abs(o.html);
if (!existsSync(htmlPath)) throw new Error(`page not found: ${htmlPath}`);
const url = pathToFileURL(htmlPath).href + '?render=1';
const log = (...a) => console.log(...a);

async function openPage() {
  const browser = await chromium.launch({ args: ['--force-color-profile=srgb', '--hide-scrollbars'] });
  const page = await browser.newPage({ viewport: { width: VIDEO.width, height: VIDEO.height }, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => { throw new Error('page error: ' + e.message); });
  page.on('console', (m) => m.type() === 'error' && console.error('[page]', m.text()));
  await page.goto(url);
  const has = await page.evaluate(() => [typeof window.__renderAt, window.__ready && typeof window.__ready.then, window.__DURATION, window.__FPS]);
  if (has[0] !== 'function' || has[1] !== 'function') throw new Error(`page breaks the contract (__renderAt/__ready): ${has}`);
  await Promise.race([page.evaluate(() => window.__ready),
    new Promise((_, rej) => setTimeout(() => rej(new Error('window.__ready timed out after 180 s')), 180000))]);
  return { browser, page, duration: has[2], fps: has[3] };
}

// lossless PNG of the canvas as drawn (raw getImageData readback is ~5x slower over CDP)
const grab = (page, t) => page.evaluate((t) => {
  window.__renderAt(t);
  return document.getElementById('stage').toDataURL('image/png');
}, t).then((u) => Buffer.from(u.slice(22), 'base64'));
const grabPng = (page, t) => grab(page, t).then((b) => 'data:image/png;base64,' + b.toString('base64'));

async function main() {
  if (o.still != null || o.sheet != null) {
    const times = o.sheet != null ? o.sheet.split(',').map(Number) : [Number(o.still)];
    if (times.some((t) => !Number.isFinite(t))) throw new Error('bad time list');
    if (!o.out) throw new Error('--out is required for --still/--sheet');
    const { browser, page } = await openPage();
    const shots = [];
    for (const t of times) shots.push(await grabPng(page, t));
    let png = shots[0];
    if (o.sheet != null) {
      const tw = Number(o.thumb), th = Math.round(tw * 9 / 16), cols = Math.min(times.length, 4), rows = Math.ceil(times.length / cols);
      png = await page.evaluate(async ({ shots, times, tw, th, cols, rows }) => {
        const c = document.createElement('canvas'); c.width = cols * tw; c.height = rows * (th + 28);
        const g = c.getContext('2d'); g.fillStyle = '#111'; g.fillRect(0, 0, c.width, c.height);
        g.font = '20px monospace'; g.textBaseline = 'middle';
        for (let i = 0; i < shots.length; i++) {
          const img = new Image(); img.src = shots[i]; await img.decode();
          const x = (i % cols) * tw, y = Math.floor(i / cols) * (th + 28);
          g.imageSmoothingQuality = 'high'; g.drawImage(img, x, y + 28, tw, th);
          g.fillStyle = '#fff'; g.fillText(`t=${times[i]}s  (frame ${Math.floor(times[i] * (window.__FPS || 24) + 1e-6)})`, x + 8, y + 14);
        }
        return c.toDataURL('image/png');
      }, { shots, times, tw, th, cols, rows });
    }
    writeFileSync(abs(o.out), Buffer.from(png.split(',')[1], 'base64'));
    await browser.close();
    log(`wrote ${abs(o.out)}`);
    return;
  }

  const t0 = Date.now();
  const first = await openPage();
  const fps = Number(o.fps ?? first.fps), pageDur = first.duration;
  const from = Number(o.from ?? 0), to = Number(o.to ?? pageDur);
  const total = Math.round((to - from) * fps), startFrame = Math.round(from * fps);
  if (!(total > 0) || to > pageDur + 1e-9) throw new Error(`bad range ${from}..${to} (page duration ${pageDur})`);
  const scale = Number(o.scale);
  const out = abs(o.out ?? `output/${VIDEO.name}.mp4`);

  // purity check: the same t must give the same pixels after drawing something else
  const probeT = (startFrame + Math.floor(total / 2)) / fps;
  const a = await grab(first.page, probeT); await grab(first.page, from);
  if (!a.equals(await grab(first.page, probeT))) console.warn('WARNING: __renderAt is NOT a pure function of t (frame differs on redraw)');
  const [W, H] = await first.page.evaluate(() => [stage.width, stage.height]);
  if (W !== VIDEO.width || H !== VIDEO.height) console.warn(`WARNING: canvas is ${W}x${H}, video.json says ${VIDEO.width}x${VIDEO.height}`);
  const ow = Math.round(W * scale / 2) * 2, oh = Math.round(H * scale / 2) * 2;

  let audio = o['no-audio'] ? null : abs(o.audio ?? 'audio/final_mix.wav');
  if (audio && !existsSync(audio)) {
    if (o.audio) throw new Error(`--audio file not found: ${audio}`);
    audio = null;
  }
  log(audio ? `audio: muxing ${audio}` : 'audio: NONE (silent video; no audio file found or --no-audio)');
  log(`render: ${total} frames, t=${from}..${to}s @ ${fps} fps, ${W}x${H} -> ${ow}x${oh}, ${o.workers} workers -> ${out}`);

  const ff = ['-v', 'error', '-y', '-f', 'image2pipe', '-c:v', 'png', '-framerate', String(fps), '-i', '-'];
  if (audio) ff.push('-ss', String(from), '-t', String(to - from), '-i', audio);
  ff.push('-map', '0:v', ...(audio ? ['-map', '1:a'] : []),
    '-vf', `${scale === 1 ? '' : `scale=${ow}:${oh}:flags=lanczos,`}scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p`,
    '-c:v', 'libx264', '-preset', o.preset, '-crf', o.crf, '-profile:v', 'high',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-fps_mode', 'cfr', '-r', String(fps), '-frames:v', String(total));
  if (audio) ff.push('-c:a', 'aac', '-b:a', '256k', '-ac', '2', '-ar', '48000');
  ff.push('-movflags', '+faststart', out);
  const enc = spawn('ffmpeg', ff, { stdio: ['pipe', 'inherit', 'inherit'] });
  const encDone = new Promise((res, rej) => { enc.on('close', (c) => (c ? rej(new Error('ffmpeg exited ' + c)) : res())); enc.stdin.on('error', rej); });

  const done = new Map(); let next = 0, written = 0, wake = [];
  const WINDOW = 48; // frames in flight, caps memory at ~400 MB
  let pumping = false;
  const pump = async () => {
    if (pumping) return;
    pumping = true;
    while (done.has(written)) {
      const b = done.get(written); done.delete(written); written++;
      if (!enc.stdin.write(b)) await new Promise((r) => enc.stdin.once('drain', r));
      if (written % Math.ceil(total / 20) === 0) log(`  ${written}/${total} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
    }
    pumping = false;
    wake.splice(0).forEach((f) => f());
  };
  const work = async (page) => {
    for (let i; (i = next++) < total;) {
      while (i - written >= WINDOW) await new Promise((r) => wake.push(r));
      done.set(i, await grab(page, (startFrame + i) / fps));
      await pump();
    }
  };
  const extra = await Promise.all(Array.from({ length: Number(o.workers) - 1 }, openPage));
  const tReady = Date.now();
  await Promise.all([first, ...extra].map((s) => work(s.page)));
  enc.stdin.end();
  await encDone;
  await Promise.all([first, ...extra].map((s) => s.browser.close()));
  log(`done: ${total} frames, ${((Date.now() - t0) / 1000).toFixed(1)}s total (${((Date.now() - tReady) / 1000).toFixed(1)}s capture+encode) -> ${out}`);
}
main().then(() => process.exit(0), (e) => { console.error(e.message); process.exit(1); });
