---
name: video-short-js
description: Builds a 30-90 second animated short as one self-contained JavaScript canvas page plus an MP4, with original score, sound design and locally generated narration. Use when asked for an animated short, explainer film, title sequence or story video in pure JavaScript.
license: MIT
---

# video-short-js

Turns a story brief into a finished short film: a single HTML file that plays the animation with
its audio, and a rendered MP4. Everything is drawn in code on one canvas. No video editor, no
framework, no cloud generation.

It was extracted from one real 60-second production (a torn-paper collage film with an original
score, 67 timed sound cues and four narrated lines). The scripts are the parts that
were the same for any film; the judgment calls are written down in `references/`.

## The five ideas that make it work

1. **The film is one pure function, `renderAt(t)`.** No timers, no state between frames, no
   `Math.random()`. Any frame can be drawn in any order, which gives you stills, contact sheets,
   parallel rendering and audio-locked playback for free.
2. **The cue sheet is written first.** `audio/CUES.md` fixes every time that picture and sound
   share, on a musical grid whose bars land on whole seconds. Picture and audio are then built
   in parallel against it and meet without re-timing.
3. **Look at frames, constantly and cheaply.** One still before any choreography; small contact
   sheets after every change. You cannot review motion you have not looked at.
4. **Borrow eyes that are not yours.** A local vision model plays a first-time viewer; an
   independent reviewer gives director's notes. Neither is told what you think the film says.
5. **The machine is part of the production.** Long builds fill disks and swap quietly. Check
   before every heavy step and delete drafts as you go.

## Start

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/new-project.sh" <target-dir> [name]   # copies the starter kit, installs playwright-core
bash "${CLAUDE_SKILL_DIR}/scripts/selftest.sh"                          # optional: proves build + render work here
```

The project is then self-contained (its own `tools/`, `src/`, `video.json`), so it can be
rebuilt later without this skill. Run every tool from the project root.

| Tool | What it does |
|---|---|
| `bash tools/preflight.sh` | disk, memory, swap; exits 1 when a render or model load would be unsafe |
| `node tools/build.mjs` | `src/*.js` + mixed audio -> `output/<name>.html`, one file |
| `node tools/shot.mjs out.png 0.25 t1 t2 ...` | one still, or a labelled contact sheet of many times |
| `node tools/render.mjs [--from a --to b] [--workers 2] [--crf 18]` | frame-exact MP4, audio muxed if `audio/final_mix.wav` exists |
| `uv run tools/mix.py` | stems -> `final_mix.wav` + `.m4a`; prints voice-over-bed margins per line |
| `python3 tools/local_viewer.py output/<name>.mp4` | a local vision model describes the film cold; nothing is downloaded |

## The process

Follow the phases in `references/process.md`. In short:

1. **Preflight and inventory.** Run `tools/preflight.sh`. List the local models that already
   exist (speech, transcription, vision) before planning any step around one. Download none
   without asking.
2. **Brief.** Put the brief in `BRIEF.md`. If the owner gave words, keep their words.
3. **Cue sheet.** Fill `audio/CUES.md`: acts, hits, narration windows, pitched cues.
4. **Dispatch audio in parallel** using the briefs in `references/agent-briefs.md`: score,
   sound design, narration. Give each the rules up front (see "Rules for every helper").
5. **Look development.** Palette, one material primitive, one character, one frame. Look at it.
6. **Build and choreograph.** Sprites cut once at load; `renderAt(t)` keyed on the cue times;
   cuts on the grid.
7. **Review loop.** Contact sheets at 0.25-0.33 scale for story, 0.5 for one shot, a debug camera
   for acting.
8. **Fresh eyes.** `tools/local_viewer.py`, then one independent director's review.
9. **Mix, render, verify.** `mix.py`, `build.mjs`, `render.mjs`, then `ffprobe` the result.
10. **Credits and a making-of page.** Every sample and model with its licence.

## Rules for every helper (subagents included)

Put these in the first brief, not in a follow-up. Each one was learned by breaking it.

- **Local models only, and only ones already installed.** Name the exact model and where it
  lives. Set `HF_HUB_OFFLINE=1`. A package that "just needs a small model" will fetch one
  silently; a transcription check did exactly that.
- **Licences are read, not assumed.** Every recording, sample set and model goes in a
  `CREDITS.md` with its source URL and licence, checked on the source page.
- **Never play audio aloud** on a machine whose owner is away. Measure instead: duration,
  loudness, true peak, onsets against the cue sheet, a spectrogram.
- **Disk and memory are shared.** No large downloads without a size estimate; delete
  intermediates; one heavy job at a time.
- **Spend tokens carefully.** Search, then read the span you need; keep command output short;
  never retry a usage-limit failure.
- **Say what you could not verify.** Nobody on this job can hear. Reports name what was
  measured and what was not.

## What good looks like before you call it done

- `ffprobe` shows the exact frame count, fps and duration, and an audio stream
- the HTML plays from a cold load in two browser engines, with audio
- every cue in `CUES.md` has a visible event at that time (check a frame at each hit)
- the local viewer's cold summary matches the brief's story, or you know why it does not
- the director's notes are each fixed or consciously declined, and you can say which
- `CREDITS.md` covers every third-party sound, sample and model
- drafts, temp frames and unused downloads are deleted

## References

- `references/process.md`: each phase in detail, with the commands
- `references/engine.md`: the drawing kit in `starter/src` (paper pieces, ink, sprites, time helpers) and how to give a film a different look
- `references/agent-briefs.md`: fill-in briefs for composer, sound designer, narrator, director
- `references/lessons.md`: measured gotchas, each with the number that taught it
