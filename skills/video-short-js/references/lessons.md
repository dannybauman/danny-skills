# Lessons, each with the number that taught it

From a 60-second, 1920x1080, 24 fps production on a 16 GB Apple Silicon laptop.

## Picture

- **Cut sprites once, draw with `drawImage`.** About 220 pre-cut sprites (360 with ink variants) built in 0.3 s
  (2 s in WebKit); frames then cost 3-8 ms in Chrome and 12 ms in WebKit. Drawing torn paper live would
  not have held 60 Hz.
- **Amber added to blue is white.** A glowing amber route drawn with additive blending read as a
  white line, and a reviewer called it "a map app". Draw the halo additively, then the amber core
  in normal blending.
- **Grade first, glow last.** Colour grading (a multiply tint for storm, dusk) goes over the
  paper world; the glow pass comes after it, so lights stay bright as the world darkens.
- **Tiling needs periodic noise.** A sea strip tiled with ordinary noise showed a seam every
  tile. Blend `noise(x)` and `noise(x - period)` across the tile so the ends meet.
- **Depth without 3D.** Layers are drawn back to front and things "stand in" the sea because the
  next strip is drawn over their foot. A horizon is just a screen-space line the sea starts at;
  lifting it away while zooming out reads as the camera rising.
- **An action must touch its effect.** Waves that crossed open water while splashes appeared on
  the islands read as two unrelated things. Each wave now travels to the shore and breaks there.
- **Interface shapes sneak in.** Expanding rings, pills, rounded line caps and selection-style
  ellipses all read as UI. In a hand-made film a confirmation is a lamp coming on or a scrap of
  paper pasted down.
- **Glow rules get bent by accident.** A translucent paper "sunbeam" was not technically a glow
  and still broke the rule for the viewer. Judge the rule by what it looks like.
- **Subtle is not the same as invisible.** A background event meant as a quiet nod was missed by
  the reviewer until it was longer and thicker.

## Sound

- **Bars on whole seconds.** 6/8 at dotted-quarter 60 gave 2.000 s bars; every cut and hit sat
  on a grid both sides could hit without negotiation. All 67 effect cues landed within 20 ms.
- **Nobody can hear.** Everything was verified by measurement: duration, LUFS, true peak, onset
  times, spectrograms, a transcript check on narration. Say so in the hand-off; a human should
  listen once before it ships.
- **Voice over bed.** With the bed ducked 7 dB under speech and the voice 3 dB down, lines sat
  +6 to +18 dB over the bed. The tightest was the last line over the fullest music.
- **A naive limiter under-limits.** Smoothing a gain-reduction curve lowers its peaks; hold the
  reduction around each peak for longer than the smoothing window.

## Render

- **Lossless capture, modest encode.** Canvas -> PNG -> one ffmpeg, frame N = t N/fps exactly.
  1440 frames took 4 minutes with 3 browser workers, and 5 minutes with 6 while the machine was
  swapping: more workers is not faster on a loaded laptop.
- **Film grain is expensive to encode.** A full-frame paper grain that re-seats 12 times a
  second made crf 15 cost 194 MB a minute. crf 18 came to 99 MB; crf 23 about 48 MB.
- **A general HTML-to-video tool was not a better renderer here.** It needed the page rebuilt
  around its own composition format and captured JPEG frames by default; a 140-line Playwright
  stepper was lossless and as fast. Evaluate, then keep the simple thing.

## Machine

- **The disk filled to 216 MB free mid-build.** Nothing announced it; a write failed. The
  causes were ordinary: a 1 GB sample library, package caches, a 194 MB draft render, and swap
  growing into what was left. Check container free space (`diskutil`, not `df`), delete drafts
  immediately, and prune sample libraries to the files actually loaded.
- **A 9B vision model took free memory from 55% to 14%.** It worked, but on a machine that was
  already swapping. Check memory, swap and disk before loading; ask for about 60% free; unload
  the moment the job ends.
- **"Already installed" must be checked by date.** A transcription model listed as pre-existing
  had been downloaded minutes earlier by a helper that was told the cache was there. Before
  calling a model local, look at when its files were created, and put the no-download rule in
  the first brief.
- **Helpers delete what they cannot see referenced.** A cleanup removed two samples that a
  script named through a variable. Ask for a dry-run list before any prune.

## Review

- **A small vision model reads four frames well and forty badly.** Per-part questions (4-5
  frames at 768 px, about 1,700 prompt tokens, 19-90 s each) gave accurate notes; the summary
  question then ran on text alone. Its cold summary matched the story and missed the threat,
  which pointed at a real weakness in the picture.
- **The independent review found what the author could not.** Ten notes, all acted on (two in part). Give
  the reviewer the brief and frames, not your opinion.
