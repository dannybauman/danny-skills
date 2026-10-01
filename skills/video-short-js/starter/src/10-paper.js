// ---------------------------------------------------------------- paper: grain, torn pieces, ink, sprites
let BOIL = 0;          // which line-boil variant is being drawn (ink wobbles, paper stays put)
let AUTO = 1;          // auto seed counter, reset per sprite so variants share their tears
const GRAIN = [];      // repeatable grain patterns
const SPR = {};        // sprite registry

function grainTile(size, seed, o) {
  const c = makeCanvas(size, size), x = c.getContext('2d'), img = x.createImageData(size, size), d = img.data;
  const pn = (u, v, per, s) => {
    const X = u * per, Y = v * per, xi = Math.floor(X), yi = Math.floor(Y), fx = X - xi, fy = Y - yi;
    const sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy), h = (a, b) => hash2((a % per) + s * 131, (b % per) + s * 977);
    return lerp(lerp(h(xi, yi), h(xi + 1, yi), sx), lerp(h(xi, yi + 1), h(xi + 1, yi + 1), sx), sy) - .5;
  };
  for (let py = 0; py < size; py++) for (let px = 0; px < size; px++) {
    const u = px / size, v = py / size;
    const n = pn(u, v, 5, seed) * o.blotch + pn(u, v, 19, seed + 1) * o.blotch * .6 + pn(u, v, 90, seed + 2) * o.mid + (hash2(px + seed * 7919, py) - .5) * o.fine;
    const i = (py * size + px) * 4, a = Math.min(255, Math.abs(n) * 255);
    const tone = n < 0 ? 20 : 255; d[i] = tone; d[i + 1] = n < 0 ? 14 : 250; d[i + 2] = n < 0 ? 8 : 236; d[i + 3] = a;
  }
  x.putImageData(img, 0, 0);
  const r = rng(seed * 31 + 7);
  for (let i = 0; i < o.fibers; i++) {
    const fx = r() * size, fy = r() * size, a = r() * TAU, L = 5 + r() * r() * 46, light = r() < .55;
    x.strokeStyle = light ? `rgba(255,252,240,${.05 + r() * .16})` : `rgba(40,28,16,${.04 + r() * .12})`;
    x.lineWidth = .5 + r() * .9;
    const bx = Math.cos(a + (r() - .5)) * L * .5, by = Math.sin(a + (r() - .5)) * L * .5;
    for (const ox of [-size, 0, size]) for (const oy of [-size, 0, size]) {
      x.beginPath(); x.moveTo(fx + ox, fy + oy); x.quadraticCurveTo(fx + ox + bx, fy + oy + by, fx + ox + Math.cos(a) * L, fy + oy + Math.sin(a) * L); x.stroke();
    }
  }
  return c;
}
function initPaper(ctx) {
  GRAIN[0] = ctx.createPattern(grainTile(512, 11, { blotch: .16, mid: .14, fine: .12, fibers: 500 }), 'repeat');   // soft cartridge paper
  GRAIN[1] = ctx.createPattern(grainTile(512, 23, { blotch: .30, mid: .20, fine: .16, fibers: 1100 }), 'repeat');  // fibrous handmade
  GRAIN[2] = ctx.createPattern(grainTile(512, 37, { blotch: .12, mid: .32, fine: .26, fibers: 220 }), 'repeat');   // rough kraft
}
const scratches = new Map();
function scratchFor(cv) {
  const k = cv.width + 'x' + cv.height; let s = scratches.get(k);
  if (!s) { s = makeCanvas(cv.width, cv.height); scratches.set(k, s); }
  return s;
}

// A piece of paper. pts: closed polygon in local units.
// o: fill, tear (edge roughness), white (width of torn white rim), shadow (0..1 strength), grain (0..2), ga (grain alpha),
//    inside(ctx) (drawn only where the paper is), ink ({..} outline), seed, step
function piece(ctx, pts, o = {}) {
  const seed = o.seed ?? (AUTO += 13);
  const tear = o.tear ?? 1, step = o.step ?? 4;
  const P = roughen(pts, tear, seed, step);
  const s = scratchFor(ctx.canvas), sx = s.getContext('2d');
  sx.setTransform(1, 0, 0, 1, 0, 0); sx.globalCompositeOperation = 'source-over'; sx.globalAlpha = 1; sx.clearRect(0, 0, s.width, s.height);
  sx.setTransform(ctx.getTransform());
  tracePoly(sx, P); sx.fillStyle = o.fill || C.paper; sx.fill();
  sx.globalCompositeOperation = 'source-atop';
  if (o.inside) { sx.save(); o.inside(sx); sx.restore(); }
  sx.save(); sx.setTransform(1, 0, 0, 1, 0, 0); sx.globalAlpha = o.ga ?? .6;
  sx.translate(-hash2(seed, 5) * 512, -hash2(seed, 6) * 512); sx.fillStyle = GRAIN[o.grain ?? 0];
  sx.fillRect(0, 0, s.width + 512, s.height + 512); sx.restore();
  const sh = o.shadow ?? .5;
  ctx.save();
  const setShadow = () => { if (sh > 0) { ctx.shadowColor = `rgba(38,28,20,${.42 * sh})`; ctx.shadowBlur = (o.blur ?? 5) * RES_NOW * .5; ctx.shadowOffsetX = 1.2 * RES_NOW * .5; ctx.shadowOffsetY = (o.drop ?? 2.6) * RES_NOW * .5; } };
  if (o.white) {
    setShadow(); tracePoly(ctx, roughen(expand(pts, o.white * .5), tear + o.white * .55, seed + 991, step)); ctx.fillStyle = C.white; ctx.fill();
    ctx.shadowColor = 'transparent';
  } else setShadow();
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = o.alpha ?? 1; ctx.drawImage(s, 0, 0);
  ctx.restore();
  if (o.ink) ink(ctx, P, Object.assign({ closed: true, seed: seed + 3, wob: .5 }, o.ink));
  return P;
}

// A hand-inked line. Width breathes, the line wanders, and it boils between sprite variants.
function ink(ctx, pts, o = {}) {
  const w = o.w ?? 1.5, seed = (o.seed ?? (AUTO += 13)) + BOIL * 7919, closed = !!o.closed;
  const P = roughen(pts, o.wob ?? .6, seed, o.step ?? 4, closed), n = P.length, m = closed ? n : n - 1, gaps = o.gaps ?? 0;
  ctx.save(); ctx.strokeStyle = o.color || C.ink; if (o.alpha != null) ctx.globalAlpha *= o.alpha; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (let i = 0; i < m; i++) {
    if (gaps && vnoise(i * .09, seed + 3) * .5 + .5 < gaps) continue;
    let lw = w * (.72 + .42 * vnoise(i * .21, seed + 9));
    if (o.taper) lw *= .25 + .75 * Math.sin(Math.PI * clamp((i + .5) / m));
    ctx.lineWidth = lw; ctx.beginPath(); ctx.moveTo(P[i][0], P[i][1]); const b = P[(i + 1) % n]; ctx.lineTo(b[0], b[1]); ctx.stroke();
  }
  ctx.restore();
}
const line = (ctx, x0, y0, x1, y1, o) => ink(ctx, [[x0, y0], [x1, y1]], o);
function dot(ctx, x, y, r, color = C.ink) { ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill(); }

// ---------------------------------------------------------------- printed papers (drawn inside a piece)
const PRINT = {
  news(ctx, x, y, w, h, seed = 1, sc = 1) {
    const r = rng(seed); ctx.fillStyle = 'rgba(52,44,38,.62)';
    const colW = 34 * sc; let cx = x + 3;
    while (cx < x + w) {
      let cy = y + 3 + r() * 6;
      if (r() < .3) { ctx.fillRect(cx, cy, colW - 6, 3.2 * sc); cy += 7 * sc; }
      while (cy < y + h) {
        if (r() < .06) { ctx.fillStyle = 'rgba(52,44,38,.28)'; ctx.fillRect(cx, cy, colW - 6, 14 * sc); ctx.fillStyle = 'rgba(52,44,38,.62)'; cy += 17 * sc; continue; }
        let lx = cx; const end = cx + colW - 6 - (r() < .2 ? r() * 14 : 0);
        while (lx < end) { const ww = (2 + r() * 6) * sc; ctx.fillRect(lx, cy, Math.min(ww, end - lx), .9 * sc); lx += ww + 1.6 * sc; }
        cy += 2.7 * sc;
      }
      cx += colW;
    }
  },
  grid(ctx, x, y, w, h, st = 8, col = 'rgba(70,120,150,.45)', lw = .5) {
    ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.beginPath();
    for (let i = x; i <= x + w; i += st) { ctx.moveTo(i, y); ctx.lineTo(i, y + h); }
    for (let j = y; j <= y + h; j += st) { ctx.moveTo(x, j); ctx.lineTo(x + w, j); }
    ctx.stroke();
  },
  stripes(ctx, x, y, w, h, st = 8, col = 'rgba(255,255,255,.5)', ang = .5, lw = 3) {
    ctx.save(); ctx.translate(x + w / 2, y + h / 2); ctx.rotate(ang); ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.beginPath();
    const R = Math.hypot(w, h); for (let i = -R; i <= R; i += st) { ctx.moveTo(i, -R); ctx.lineTo(i, R); } ctx.stroke(); ctx.restore();
  },
  dots(ctx, x, y, w, h, st = 9, col = 'rgba(255,255,255,.6)', rad = 1.6) {
    ctx.fillStyle = col; let row = 0;
    for (let j = y; j <= y + h; j += st * .86, row++) for (let i = x + (row & 1 ? st / 2 : 0); i <= x + w; i += st) { ctx.beginPath(); ctx.arc(i, j, rad, 0, TAU); ctx.fill(); }
  },
  // a scrap of topographic map: contour rings, a river, a road
  map(ctx, x, y, w, h, seed = 1, sc = 1) {
    const r = rng(seed);
    ctx.lineWidth = .6 * sc; ctx.strokeStyle = 'rgba(150,104,60,.55)';
    for (let k = 0; k < 3; k++) {
      const cx = x + r() * w, cy = y + r() * h, R = (14 + r() * 26) * sc;
      for (let j = 1; j <= 4; j++) { tracePoly(ctx, blob(cx, cy, R * j / 3.2, R * j / 4, seed + k * 9, .22, 26)); ctx.stroke(); }
    }
    ctx.strokeStyle = 'rgba(54,128,150,.8)'; ctx.lineWidth = 1.6 * sc;
    const ry = y + h * (.3 + r() * .4);
    tracePoly(ctx, curve([[x - 5, ry], [x + w * .3, ry + (r() - .5) * h * .5], [x + w * .65, ry + (r() - .5) * h * .5], [x + w + 5, ry + (r() - .5) * h * .4]], false, 8), false); ctx.stroke();
    ctx.strokeStyle = 'rgba(190,84,60,.7)'; ctx.lineWidth = .9 * sc; ctx.setLineDash([4 * sc, 2 * sc]);
    ctx.beginPath(); ctx.moveTo(x + r() * w, y - 2); ctx.lineTo(x + r() * w, y + h + 2); ctx.stroke(); ctx.setLineDash([]);
  },
  corrug(ctx, x, y, w, h, st = 4, col = 'rgba(80,52,28,.28)') {
    ctx.strokeStyle = col; ctx.lineWidth = 1; ctx.beginPath(); for (let i = x; i <= x + w; i += st) { ctx.moveTo(i, y); ctx.lineTo(i, y + h); } ctx.stroke();
  },
  wash(ctx, x, y, w, h, col, seed = 1, n = 5, wrap = 0) {         // uneven watercolour blooms
    const r = rng(seed);
    for (let i = 0; i < n; i++) {
      const cx = x + r() * w, cy = y + r() * h, R = (.25 + r() * .5) * Math.min(Math.max(w, h), 420);
      for (const ox of wrap ? [-wrap, 0, wrap] : [0]) {
        const g = ctx.createRadialGradient(cx + ox, cy, 0, cx + ox, cy, R); g.addColorStop(0, col); g.addColorStop(1, col.replace(/[\d.]+\)$/, '0)'));
        ctx.fillStyle = g; ctx.fillRect(cx + ox - R, cy - R, R * 2, R * 2);
      }
    }
  },
};
// masking tape holding something down
function tape(ctx, x, y, w, h, rot = 0, seed) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
  piece(ctx, rect(-w / 2, -h / 2, w, h), { fill: '#eadfbd', tear: .9, shadow: .25, alpha: .82, seed, step: 2.5, ga: .8, grain: 1 });
  ctx.restore();
}

// ---------------------------------------------------------------- sprites
// bounds in local world units; local origin is the anchor
function sprite(name, x0, y0, x1, y1, draw, o = {}) {
  const res = o.res ?? RES, n = o.variants ?? 1, pad = o.pad ?? 10;
  x0 -= pad; y0 -= pad; x1 += pad; y1 += pad;
  const s = SPR[name] = { x0, y0, w: x1 - x0, h: y1 - y0, res, frames: [] };
  for (let v = 0; v < n; v++) {
    const c = makeCanvas((x1 - x0) * res, (y1 - y0) * res), ctx = c.getContext('2d');
    ctx.setTransform(res, 0, 0, res, -x0 * res, -y0 * res);
    BOIL = v; AUTO = (o.seed ?? (name.length * 131 + name.charCodeAt(0) * 17 + name.charCodeAt(name.length - 1))) * 101;
    const keep = RES_NOW; RES_NOW = res; draw(ctx, v); RES_NOW = keep;
    s.frames.push(c);
  }
  BOIL = 0;
  return s;
}
let RES_NOW = RES;
let FRAME_BOIL = 0;    // set per frame by the renderer
function spr(ctx, name, x, y, o) {
  const s = SPR[name]; if (!s) return;
  const f = s.frames[((o && o.v != null ? o.v : FRAME_BOIL) + (o && o.vo || 0)) % s.frames.length];
  if (!o) { ctx.drawImage(f, x + s.x0, y + s.y0, s.w, s.h); return; }
  ctx.save(); ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot);
  if (o.sx != null || o.sy != null) ctx.scale(o.sx ?? 1, o.sy ?? o.sx ?? 1);
  if (o.alpha != null) ctx.globalAlpha *= o.alpha;
  ctx.drawImage(f, s.x0, s.y0, s.w, s.h);
  ctx.restore();
}
