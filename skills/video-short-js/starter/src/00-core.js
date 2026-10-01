'use strict';
// ---------------------------------------------------------------- constants
// VIDEO is video.json, injected by tools/build.mjs. One film = one canvas = one pure function renderAt(t)
const W = VIDEO.width, H = VIDEO.height, DUR = VIDEO.duration, FPS = VIDEO.fps;
const RES = 2;                 // sprite pixels per world unit: raise it if your camera zooms in past 2x
const TAU = Math.PI * 2;
const stage = document.getElementById('stage'), ctx = stage.getContext('2d');

// the palette. Replace it: a film's look starts here
const C = {
  paper: '#f3ead8', white: '#f8f3e7', ink: '#2b2622',
  sand: '#e2c795', kraft: '#b98d5e', clay: '#c96f4a', moss: '#7d9a5c', mustard: '#d9a441', rose: '#d99a8a',
  sea0: '#173a55', sea1: '#1f4e6b', sea2: '#256478', sea3: '#2c7b84', sea4: '#4f9a99', sea5: '#86bdb4',
  foam: '#f4efe2', amber: '#ffb648',
};

// ---------------------------------------------------------------- math
const clamp = (v, a = 0, b = 1) => v < a ? a : v > b ? b : v;
const lerp = (a, b, t) => a + (b - a) * t;
const seg = (t, a, b) => clamp((t - a) / (b - a));           // 0..1 progress of t through [a,b]
const smooth = t => t * t * (3 - 2 * t);
const easeIO = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const easeO = t => 1 - Math.pow(1 - t, 3);
const easeI = t => t * t * t;
const backO = t => { const c = 1.9; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
const pulse = (t, a, b, c, d) => smooth(seg(t, a, b)) * (1 - smooth(seg(t, c, d)));   // up a..b, down c..d
// stop-motion time: everything that is "a puppet" moves on twos (12 poses per second)
const q = (t, fps = 12) => Math.floor(t * fps + 1e-6) / fps;

function hash(n) {
  n = Math.imul(n ^ (n >>> 16), 0x45d9f3b); n = Math.imul(n ^ (n >>> 16), 0x45d9f3b); n ^= n >>> 16;
  return (n >>> 0) / 4294967296;
}
const hash2 = (a, b) => hash((Math.imul(a | 0, 374761393) + Math.imul(b | 0, 668265263)) | 0);
function rng(seed) { let i = 0; return () => hash2(seed, ++i); }
function vnoise(x, seed) { const i = Math.floor(x), f = x - i; return lerp(hash2(i, seed), hash2(i + 1, seed), f * f * (3 - 2 * f)) * 2 - 1; }
function fbm(x, seed, oct = 3) { let a = 0, amp = 1, fr = 1, n = 0; for (let o = 0; o < oct; o++) { a += vnoise(x * fr, seed + o * 17) * amp; n += amp; amp *= .5; fr *= 2; } return a / n; }

// keyframe track: [[t, v, ease?], ...]; ease applies to the segment arriving at that key
function track(t, keys) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    if (t < keys[i][0]) { const a = keys[i - 1], b = keys[i]; return lerp(a[1], b[1], (b[2] || easeIO)(seg(t, a[0], b[0]))); }
  }
  return keys[keys.length - 1][1];
}
const hold = t => 0, linear = t => t, snap = t => t < 1 ? 0 : 1;

// ---------------------------------------------------------------- canvas helpers
function makeCanvas(w, h) { const c = document.createElement('canvas'); c.width = Math.ceil(w); c.height = Math.ceil(h); return c; }
function tracePoly(ctx, pts, closed = true) {
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
  if (closed) ctx.closePath();
}
function rgba(hex, a) { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16},${n >> 8 & 255},${n & 255},${a})`; }
function mix(h1, h2, t) {
  const a = parseInt(h1.slice(1), 16), b = parseInt(h2.slice(1), 16);
  const r = Math.round(lerp(a >> 16, b >> 16, t)), g = Math.round(lerp(a >> 8 & 255, b >> 8 & 255, t)), bl = Math.round(lerp(a & 255, b & 255, t));
  return '#' + ((1 << 24) | (r << 16) | (g << 8) | bl).toString(16).slice(1);
}

// ---------------------------------------------------------------- shape helpers (all return [[x,y],...])
// closed Catmull-Rom through control points
function curve(ctrl, closed = true, per = 10) {
  const n = ctrl.length, out = [];
  const P = i => closed ? ctrl[(i % n + n) % n] : ctrl[clamp(i, 0, n - 1)];
  const last = closed ? n : n - 1;
  for (let i = 0; i < last; i++) {
    const p0 = P(i - 1), p1 = P(i), p2 = P(i + 1), p3 = P(i + 2);
    for (let j = 0; j < per; j++) {
      const t = j / per, t2 = t * t, t3 = t2 * t;
      out.push([
        .5 * (2 * p1[0] + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
        .5 * (2 * p1[1] + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)]);
    }
  }
  if (!closed) out.push(ctrl[n - 1].slice());
  return out;
}
function ellipse(cx, cy, rx, ry, n = 28, a0 = 0, a1 = TAU) {
  const out = []; for (let i = 0; i < n; i++) { const a = a0 + (a1 - a0) * i / n; out.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]); } return out;
}
// irregular blob: ellipse with low-frequency radial wobble
function blob(cx, cy, rx, ry, seed, wob = .12, n = 40) {
  const out = []; for (let i = 0; i < n; i++) {
    const a = i / n * TAU, k = 1 + wob * (Math.sin(a * 2 + hash2(seed, 1) * 9) * .5 + Math.sin(a * 3 + hash2(seed, 2) * 9) * .35 + Math.sin(a * 5 + hash2(seed, 3) * 9) * .2);
    out.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k]);
  } return out;
}
const rect = (x, y, w, h) => [[x, y], [x + w, y], [x + w, y + h], [x, y + h]];
const quad = (x, y, w, h, skew = 0, taper = 0) => [[x + skew + taper, y], [x + w + skew - taper, y], [x + w, y + h], [x, y + h]];
function xf(pts, dx = 0, dy = 0, rot = 0, sx = 1, sy = sx) {
  const c = Math.cos(rot), s = Math.sin(rot);
  return pts.map(([x, y]) => { x *= sx; y *= sy; return [x * c - y * s + dx, x * s + y * c + dy]; });
}
// subdivide + displace along normal: the tear
function roughen(pts, amp, seed, step = 5, closed = true) {
  if (amp <= 0) return pts;
  const out = [], n = pts.length; let dist = 0;
  const last = closed ? n : n - 1;
  for (let i = 0; i < last; i++) {
    const a = pts[i], b = pts[(i + 1) % n], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1e-6;
    const k = Math.max(1, Math.round(L / step)), nx = dy / L, ny = -dx / L;
    for (let j = 0; j < k; j++) {
      const u = j / k, d = dist + L * u;
      const o = amp * (fbm(d * .045, seed, 2) * .9 + fbm(d * .33, seed + 5, 2) * .55);
      out.push([a[0] + dx * u + nx * o, a[1] + dy * u + ny * o]);
    }
    dist += L;
  }
  if (!closed) out.push(pts[n - 1].slice());
  return out;
}
// grow a closed polygon outward by d
function expand(pts, d) {
  let area = 0; const n = pts.length;
  for (let i = 0; i < n; i++) { const a = pts[i], b = pts[(i + 1) % n]; area += a[0] * b[1] - b[0] * a[1]; }
  const sgn = area > 0 ? 1 : -1;
  return pts.map((p, i) => {
    const a = pts[(i - 1 + n) % n], b = pts[(i + 1) % n], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1e-6;
    return [p[0] + dy / L * d * sgn, p[1] - dx / L * d * sgn];
  });
}
function polyLen(pts) { let L = 0; for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); return L; }
// point at arc-length fraction u along an open polyline; returns [x,y,angle]
function along(pts, u) {
  const L = polyLen(pts); let d = clamp(u) * L;
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1], b = pts[i], l = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (d <= l || i === pts.length - 1) { const k = l ? clamp(d / l) : 0; return [lerp(a[0], b[0], k), lerp(a[1], b[1], k), Math.atan2(b[1] - a[1], b[0] - a[0])]; }
    d -= l;
  }
}
function bezier(p0, p1, p2, p3, n = 24) {
  const out = []; for (let i = 0; i <= n; i++) {
    const t = i / n, m = 1 - t;
    out.push([m * m * m * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t * t * t * p3[0], m * m * m * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t * t * t * p3[1]]);
  } return out;
}
