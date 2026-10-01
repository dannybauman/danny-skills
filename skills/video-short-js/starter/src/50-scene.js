// ---------------------------------------------------------------- the scene
// The whole film is renderAt(t): a pure function of time. No timers, no state carried between frames,
// no Math.random(), no Date. That is what lets any frame be drawn in any order, in any tab,
// for stills, contact sheets, parallel rendering and audio-locked playback.
// This starter scene is eight seconds: a paper boat crosses a paper sea and leaves a glowing route.
// Replace it. Keep the two entry points: buildAll() cuts the sprites once, renderAt(t) draws a frame.

const CUE = { depart: 1.0, arrive: 6.33, ting: [2.0, 3.0, 4.0, 5.0] };          // must match audio/CUES.md
const ROUTE = bezier([260, 720], [700, 840], [1220, 600], [1660, 700], 40);

function buildAll() {
  // sea: five strips of torn paper, darker toward us. One sprite each, two ink variants for line boil
  ['#86bdb4', '#4f9a99', '#2c7b84', '#256478', '#1f4e6b'].forEach((col, i) => sprite('strip' + i, 0, -24, W + 160, 260, (c) => {
    const top = []; for (let x = -10; x <= W + 170; x += 6) top.push([x, Math.sin(x * .011 + i * 2) * 9 + Math.sin(x * .031 + i) * 4]);
    piece(c, top.concat([[W + 170, 280], [-10, 280]]), { fill: col, tear: 1.4, white: 2.4, shadow: .5, grain: 1, ga: .75, seed: 20 + i, inside: k => PRINT.wash(k, 0, 0, W, 260, 'rgba(255,255,255,.14)', i + 3, 6) });
    const r = rng(i + 40); for (let n = 0; n < 12; n++) { const x = 60 + r() * (W - 120), y = 30 + r() * 60; ink(c, curve([[x, y], [x + 9, y - 3], [x + 18, y], [x + 27, y + 3], [x + 36, y]], false, 5), { w: 1.1, color: mix(col, '#0e2233', .5), alpha: .5, seed: n + i * 20, wob: .4 }); }
  }, { res: 1, pad: 0, variants: 2 }));
  sprite('sun', -80, -80, 80, 80, (c) => {
    for (let i = 0; i < 14; i++) { const a = i / 14 * TAU; line(c, Math.cos(a) * 50, Math.sin(a) * 50, Math.cos(a) * 66, Math.sin(a) * 66, { w: 2, color: '#d9933f', seed: i }); }
    piece(c, ellipse(0, 0, 40, 40, 36), { fill: '#f4c35f', tear: .8, white: 1.6, shadow: .35, grain: 1 });
  }, { variants: 3 });
  sprite('boat', -90, -160, 90, 14, (c) => {
    ink(c, [[0, -24], [1.5, -90], [0, -150]], { w: 3.4, color: '#6b4a36', wob: .5 });
    piece(c, [[6, -146], [80, -46], [6, -40]], { fill: '#f1e6cd', tear: 1, shadow: .5, grain: 1, inside: k => PRINT.grid(k, 0, -150, 90, 120, 9) });
    piece(c, [[-6, -130], [-6, -44], [-54, -44]], { fill: C.mustard, tear: 1, shadow: .5, grain: 1 });
    piece(c, [[-76, -30], [82, -34], [56, 8], [-52, 8]], { fill: '#efe3c8', tear: .9, shadow: .5, grain: 1, inside: k => PRINT.news(k, -80, -36, 170, 48, 5, .8) });
  }, { variants: 3 });
  const g = SPR.glow = { x0: -128, y0: -128, w: 256, h: 256, res: 1, frames: [makeCanvas(256, 256)] }, gx = g.frames[0].getContext('2d'), gr = gx.createRadialGradient(128, 128, 0, 128, 128, 128);
  gr.addColorStop(0, 'rgba(255,214,140,.95)'); gr.addColorStop(.3, 'rgba(255,170,70,.25)'); gr.addColorStop(1, 'rgba(255,150,40,0)'); gx.fillStyle = gr; gx.fillRect(0, 0, 256, 256);
}

function renderAt(t) {
  FRAME_BOIL = Math.floor(t * 6) % 3;                       // ink lines re-drawn six times a second
  const tq = q(t);                                          // puppets move on twos: 12 poses a second
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = '#f4e3c8'; ctx.fillRect(0, 0, W, H);
  spr(ctx, 'sun', 1500, 210, { rot: tq * .05 });
  const u = easeIO(seg(t, CUE.depart, CUE.arrive)), p = along(ROUTE, u), boatRow = 2;
  for (let i = 0; i < 5; i++) {
    spr(ctx, 'strip' + i, -80 + Math.sin(tq * .8 + i * 1.3) * 26, 420 + i * 130 + Math.sin(tq * 1.1 + i * 1.9) * 5, { v: (i + FRAME_BOIL) % 2 });
    if (i === boatRow) spr(ctx, 'boat', p[0], p[1] + Math.sin(tq * 2.1) * 3, { rot: Math.sin(tq * 1.7) * .04 });     // drawn between strips, so the next strip laps its hull
  }
  // the only thing that glows. Halo first, additively; then the amber ink on top in normal blending,
  // because amber added to a blue sea turns white
  const done = ROUTE.filter((_, i) => i / (ROUTE.length - 1) <= Math.max(0, u - .04));
  if (done.length > 1) {
    ctx.globalCompositeOperation = 'lighter'; tracePoly(ctx, done, false); ctx.strokeStyle = 'rgba(255,150,50,.16)'; ctx.lineWidth = 24; ctx.stroke();
    ctx.globalCompositeOperation = 'source-over'; ctx.setLineDash([26, 18]); ctx.strokeStyle = 'rgba(255,190,88,.96)'; ctx.lineWidth = 5; ctx.stroke(); ctx.setLineDash([]);
  }
  ctx.globalCompositeOperation = 'lighter';
  for (const at of CUE.ting) if (t >= at) { const w = along(ROUTE, easeIO(seg(at, CUE.depart, CUE.arrive))), k = 1 - easeO(seg(t, at, at + .5)); ctx.globalAlpha = .9; const R = 22 + 50 * k; ctx.drawImage(SPR.glow.frames[0], w[0] - R, w[1] - R, R * 2, R * 2); }
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  // paper grain over everything, re-seated on twos; fade in and out
  const f = Math.floor(t * 12); ctx.globalAlpha = .3; ctx.fillStyle = GRAIN[0]; ctx.save(); ctx.translate(-((hash2(f, 1) * 512) | 0), -((hash2(f, 2) * 512) | 0)); ctx.fillRect(0, 0, W + 512, H + 512); ctx.restore();
  const fade = Math.max(1 - smooth(seg(t, 0, .8)), smooth(seg(t, DUR - .8, DUR - .05)));
  if (fade > 0) { ctx.globalAlpha = fade; ctx.fillStyle = C.paper; ctx.fillRect(0, 0, W, H); } ctx.globalAlpha = 1;
}
