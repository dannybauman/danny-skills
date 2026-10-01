# The drawing kit

`starter/src/00-core.js` and `10-paper.js` are a small kit for a hand-made paper look. They are
plain functions on a 2D canvas; nothing is hidden. Keep them, change them, or replace
`10-paper.js` with another material entirely.

## Time

| Helper | Use |
|---|---|
| `seg(t, a, b)` | 0..1 progress of t through [a, b] |
| `pulse(t, a, b, c, d)` | up over a..b, down over c..d |
| `track(t, [[t0, v0], [t1, v1, ease], ...])` | keyframes; ease applies to the segment arriving at that key |
| `q(t, fps = 12)` | stop-motion time: holds each pose for a twelfth of a second |
| `smooth`, `easeIO`, `easeO`, `easeI`, `backO`, `snap` | easing |
| `hash2(a, b)`, `rng(seed)`, `vnoise`, `fbm` | deterministic randomness. Never `Math.random()` |

## Shapes (all return `[[x, y], ...]`)

`curve(ctrl, closed, per)` Catmull-Rom through control points, `ellipse`, `blob` (irregular),
`rect`, `quad` (skew and taper), `xf` (move, rotate, scale), `roughen` (the tear), `expand`,
`bezier`, `along(pts, u)` (point and angle at an arc-length fraction), `polyLen`.

## Paper

```js
piece(ctx, pts, { fill, tear, white, shadow, grain, ga, inside, ink, seed, step, alpha });
```

One piece of paper: `tear` roughens the edge, `white` adds the torn white rim, `shadow` lifts it
off the layer below, `grain` picks one of three paper textures, `inside(ctx)` prints on the
paper only where the paper is (`PRINT.news`, `grid`, `stripes`, `dots`, `map`, `corrug`, `wash`).

```js
ink(ctx, pts, { w, color, wob, taper, gaps, closed, seed });   // a hand-inked line that breathes
```

## Sprites

```js
sprite('boat', x0, y0, x1, y1, (ctx, variant) => { ... }, { variants: 3, res: 2 });
spr(ctx, 'boat', x, y, { rot, sx, sy, alpha });
```

Bounds are in world units around a local origin (the anchor). `variants` re-runs the draw with a
different ink seed while the paper stays put, so cycling variants gives line boil for free.
Set `FRAME_BOIL` once per frame; `spr` uses it.

## Glow

Keep a short list of things that may glow and draw them in one final pass, after any colour
grading. Additive blending (`'lighter'`) turns amber on blue into white: draw the soft halo
additively, then the coloured core in normal blending on top.

## A different look

The pipeline does not care what the pixels are. For another style, keep `00-core.js`, the player
and the tools, and replace `10-paper.js`:

- **Flat vector:** `piece` without tear, grain or rim; no boil; camera on ones throughout
- **Chalkboard:** dark ground, `ink` with high `wob` and `gaps`, a dust grain overlay
- **Blueprint / diagram:** one paper, one ink colour, `PRINT.grid`, lines drawn on with `along`
- **Photo collage:** load images as sprites (inline them as data URLs so the page stays one file)

Whatever the look: cut sprites once, keep `renderAt(t)` pure, and decide early what is allowed
to glow.
