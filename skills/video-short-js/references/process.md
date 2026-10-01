# The process, phase by phase

The order matters more than the detail: brief, then cue sheet, then sound and picture in parallel.

In local-first mode (`local-first.md`) the phases are the same but who does them changes: a script runs the
units, the local model writes the cue sheet, shots, notes and reviews, and the cloud makes a few logged
one-shot calls. Where a phase below says to dispatch helpers or ask an independent reviewer, use a local
unit or a one-shot call instead: helpers and supervising sessions are what made the cloud cost in that mode.

## 1. Preflight and inventory

```bash
bash tools/preflight.sh
```

Then find out what local models exist before planning around any: text-to-speech, transcription,
vision. Read the model folders rather than starting the apps that own them. Decide per step:

| Step | Needs a model? |
|---|---|
| Timing, layout, loudness, onset checks, frame counts | No. These are arithmetic. Never spend a model on them |
| Narration | Local TTS, already installed |
| Checking narration says the right words | Local transcription, already installed |
| "Can a stranger follow this?" | Local vision model, already installed |
| Composition, sound design, drawing, review | Whatever you are running on; in local-first mode the local model writes notes, events and placements, and drawing comes from a parts kit |

If a needed local model is missing, say so and ask. Do not download one on your own.

## 2. Brief

`BRIEF.md` holds the brief. Reviewers and subagents read it, so it must stand alone. Pull out,
explicitly: the feeling to land on, the feeling to avoid, any "never show" rules, and any rule
about what is allowed to glow, move or speak. Those are the lines reviews are judged against.

## 3. Cue sheet

`audio/CUES.md` is the contract. Choose the tempo so bars land on whole seconds; put every act
boundary, cut, hit and pitched cue on that grid. Give narration lines a start and a must-end-by.
Improve suggested narration only by tightening; shorter lines survive music.

Write it before any audio or animation. Once helpers are working from it, do not move a cue
without telling them.

## 4. Dispatch audio in parallel

Three independent jobs, each producing one stem of exactly the film's length, sample 0 = t 0:

- `audio/stems/score.wav`: an original composition rendered from licensed samples or synthesis
- `audio/stems/sfx.wav`: recordings and synthesis placed on the cue times, plus `events.json`
- `audio/stems/vo.wav`: narration from a local TTS model, plus `audio/vo/lines.json` with each
  line's `start` and `measured_end` (the mixer ducks the bed under these)

Briefs are in `agent-briefs.md`. Start them before you draw anything; they take as long as the
picture does. A fourth helper can prove the render tool on a stand-in page meanwhile.

## 5. Look development

Before choreography exists: palette, one material primitive, one prop, one character, one frame.
Capture it and look. Then a close-up. Fix the look here, where a change costs one sprite, and not
after forty sprites share the mistake.

## 6. Build and choreograph

- Cut every sprite once at load into an offscreen canvas; drawing a frame should be mostly
  `drawImage`. Target under 8 ms a frame so live playback holds 60 Hz.
- Key all motion on the cue times. Put the times in one table at the top of the scene file.
- Puppets move on twos (`q(t)`, 12 poses a second); cameras move on ones. Ink re-draws a few
  times a second from pre-cut variants ("boil").
- Cuts go on the musical grid. A cut is cheaper and clearer than a fast camera move.
- Keep a debug camera (`window.__cam`) so `shot.mjs cam=x,y,z` can inspect acting up close.

## 7. Review loop

```bash
node tools/build.mjs && node tools/shot.mjs /tmp/sheet.png 0.25 1 5 9 13 17 21
```

- 0.25-0.33 scale sheets answer story and composition questions and are cheap to read
- 0.5 scale for one shot's staging
- a run of consecutive frames (every 1/12 s) to check an action lands on its cue
- check one frame at every hit in the cue sheet

## 8. Fresh eyes

**A first-time viewer.** `python3 tools/local_viewer.py output/<name>.mp4` shows a local vision
model a few frames at a time and asks what is happening, then asks what the film was about from
its own notes. It is told nothing. Compare its summary with the brief: what it misses, a human
may miss too. It needs a draft MP4, about 60% free memory, and a few GB of free disk.

**A director.** One independent reviewer, given the brief and three contact sheets, asked for at
most ten ranked notes with a time and a concrete fix each. Do not give it your own opinion of
the film. Expect notes about things you stopped seeing: actions that do not connect, elements
that look like interface, rules from the brief you bent.

## 9. Mix, render, verify

```bash
uv run tools/mix.py                 # prints how far each spoken line sits above the bed
node tools/build.mjs
bash tools/preflight.sh && node tools/render.mjs --workers 2 --crf 18
ffprobe -v error -show_entries stream=codec_name,r_frame_rate,nb_frames,duration -of csv=p=0 output/<name>.mp4
```

A voice wants roughly 6 dB or more over the bed underneath it; less than that, duck more or
thin the arrangement. Integrated loudness is set to -16 LUFS with peaks under -1.5 dBFS.

Open the HTML in a second browser engine too (Playwright's WebKit works) and confirm the audio
element loads and frames draw.

## 10. Credits and making-of

Collect each helper's `CREDITS.md` into one list: source, licence, what it was used for. If a
making-of page is wanted, write it last, from measured facts, and include what went wrong.
