// ---------------------------------------------------------------- boot + player
// The page contract the tools rely on:
//   ?render=1            canvas only, no audio, no loop
//   window.__ready       Promise, resolves when sprites are built
//   window.__renderAt(t) draws the frame for time t; pure function of t
//   window.__DURATION, window.__FPS
const RENDER = new URLSearchParams(location.search).has('render');
if (RENDER) document.body.classList.add('render');
window.__DURATION = DUR; window.__FPS = FPS;
window.__renderAt = t => renderAt(clamp(t, 0, DUR - 1e-4));
ctx.fillStyle = C.paper; ctx.fillRect(0, 0, W, H);                 // paper first, while the sprites are cut

function buildUI() {                                                // the only interface: one cut-paper button
  sprite('ui_play', -90, -90, 90, 90, (c) => {
    piece(c, blob(0, 0, 70, 70, 4, .05, 40), { fill: C.paper, tear: 2.2, white: 3, shadow: .9, grain: 1, blur: 9, drop: 5 });
    piece(c, [[-20, -32], [36, 0], [-20, 32]], { fill: C.clay, tear: 1.2, shadow: .4, grain: 1, step: 3 });
  }, { variants: 3 });
  sprite('ui_again', -70, -70, 70, 70, (c) => {
    piece(c, blob(0, 0, 50, 50, 4, .05, 40), { fill: C.paper, tear: 2, white: 2.4, shadow: .9, grain: 1, blur: 9, drop: 5 });
    ink(c, ellipse(0, 0, 21, 21, 26, -1.1, 3.6), { w: 4.2, color: C.clay, wob: .6 });
    piece(c, [[4, -30], [22, -19], [5, -9]], { fill: C.clay, tear: .8, shadow: 0, step: 3 });
  }, { variants: 3 });
}

window.__ready = new Promise(resolve => setTimeout(() => {
  const t0 = performance.now(); initPaper(ctx); buildAll(); buildUI(); window.__buildMs = performance.now() - t0;
  if (RENDER) renderAt(Number(new URLSearchParams(location.search).get('t')) || 0); else startPlayer();
  resolve();
}, 30));

function startPlayer() {
  const snd = document.getElementById('snd'), hasAudio = !!snd.getAttribute('src');
  let state = 'poster', base = 0, started = 0, hideTimer = 0, endedAt = 0, lastTick = -1;       // poster | playing | paused | ended
  const now = () => performance.now() / 1000;
  const time = () => state === 'playing' ? clamp(base + now() - started, 0, DUR) : base;
  function overlay(name) { ctx.setTransform(1, 0, 0, 1, 0, 0); FRAME_BOIL = Math.floor(now() * 5) % 3; spr(ctx, name, W / 2, H / 2, { rot: Math.sin(Math.floor(now() * 5) * 1.7) * .03 }); }
  function frame() {
    // when nothing is moving, redraw only as often as the paper button wobbles
    if (state !== 'playing') { const tick = Math.floor(now() * 5); if (tick === lastTick) return requestAnimationFrame(frame); lastTick = tick; }
    if (state === 'poster') { renderAt(VIDEO.poster ?? 1); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = rgba(C.paper, .34); ctx.fillRect(0, 0, W, H); overlay('ui_play'); }
    else {
      let t = time();
      if (state === 'playing' && hasAudio && !snd.paused) { const d = snd.currentTime - t; if (Math.abs(d) > .08) { base = snd.currentTime; started = now(); t = base; } }   // the sound is the clock
      if (t >= DUR - .02 && state !== 'ended') { state = 'ended'; base = DUR - .02; t = base; endedAt = now(); }
      renderAt(Math.min(t, DUR - .02));
      if (state === 'paused') overlay('ui_play');
      if (state === 'ended' && now() - endedAt > 1.2) overlay('ui_again');
    }
    requestAnimationFrame(frame);
  }
  function play(from) { base = from; started = now(); state = 'playing'; if (hasAudio) { try { snd.currentTime = from; } catch (e) { } const p = snd.play(); if (p && p.catch) p.catch(() => { }); } }
  function toggle() { if (state === 'poster' || state === 'ended') play(0); else if (state === 'playing') { base = time(); state = 'paused'; if (hasAudio) snd.pause(); } else play(base); }
  stage.addEventListener('click', toggle);
  addEventListener('keydown', e => {
    if (e.code === 'Space' || e.key === 'k') { e.preventDefault(); toggle(); }
    else if (e.key === 'f') { if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen().catch(() => { }); }
    else if (e.key === 'r' || e.key === 'Home') play(0);
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { const t = clamp(time() + (e.key === 'ArrowLeft' ? -5 : 5), 0, DUR - .1); if (state === 'playing') play(t); else { base = t; state = 'paused'; lastTick = -1; } }
  });
  addEventListener('mousemove', () => { stage.style.cursor = 'pointer'; clearTimeout(hideTimer); hideTimer = setTimeout(() => { if (state === 'playing') stage.style.cursor = 'none'; }, 1800); });
  requestAnimationFrame(frame);
}
