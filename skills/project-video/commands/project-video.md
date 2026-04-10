---
name: project-video
description: Generates short highlight reel videos for software projects. Use when the user wants a project video, demo reel, highlight video, showcase, or changelog video for a GitHub repo.
---

# project-video

Generates polished 45-75 second highlight reel videos for any software project. Given a GitHub repo URL or local path, researches the project, builds a narrative arc, renders scene PNGs with Pillow, and assembles with FFmpeg.

## Usage

```bash
# Project showcase (default)
./run.sh --repo https://github.com/user/cool-app

# With live app screenshot
./run.sh --repo https://github.com/user/cool-app --url https://cool-app.vercel.app

# Comparison mode
./run.sh compare https://github.com/user/repo1 https://github.com/user/repo2

# Changelog / sprint recap
./run.sh changelog --repo https://github.com/user/app --since "last week"

# Dry run (PNGs only, no FFmpeg)
./run.sh --repo https://github.com/user/app --dry-run

# Clean/minimal mode (no extra effects)
./run.sh --repo https://github.com/user/app --no-extra
```

## Options

- `--repo URL` — GitHub repo URL or local path (required for showcase/changelog)
- `--url URL` — Deployed app URL for live screenshots
- `--output PATH` — Output MP4 path (default: `output/project_video.mp4`)
- `--theme NAME` — Color theme: `midnight` (default), `aurora`, `ember`, `mono`
- `--dry-run` — Generate scene PNGs only, skip FFmpeg assembly
- `--no-extra` — Disable extra visual effects (sparks, lasers, fog, etc.). Extra mode is ON by default.
- `compare` — Comparison mode: pass 2+ repo URLs after the subcommand
- `changelog` — Sprint recap mode: uses `--since` to filter recent PRs

## Modes

**Showcase** (default): Title hook, problem/context, tech stack, architecture, 2-4 feature cards, live demo screenshot, stats, closing with repo URL.

**Comparison**: Title, experiment setup, per-repo cards with stats + optional screenshots, findings, verdict, closing.

**Changelog**: Title ("What shipped"), per-PR cards with diff stats, summary stats, closing.

## Instructions for Claude

### Workflow

1. **Research first.** Run `research_project.py` to gather repo data. Review the JSON output — it contains everything needed for the video.
2. **Propose the narrative.** Based on the research, propose the scene sequence to the user. Ask 1-2 clarifying questions: "What's the most important feature to highlight?" and "Is there a live URL?"
3. **Generate.** Once the user confirms, run `generate_video.py` with the research JSON piped in or saved to a temp file.
4. **Review.** Use `--dry-run` first if the user wants to preview individual scene PNGs before final assembly.

### Research step

```bash
cd skills/project-video
python3 scripts/research_project.py --repo https://github.com/user/app > /tmp/project_research.json
```

### Generation step

```bash
cd skills/project-video
./run.sh --repo https://github.com/user/app --output output/demo.mp4
```

The script handles research + rendering in one pass. To customize scenes, edit the research JSON and pass it with `--research /tmp/project_research.json`.

### Screenshots

Screenshots are optional. If Playwright is not installed, the skill generates text-only cards. To enable screenshots:

```bash
pip install playwright && playwright install chromium
```

Then pass `--url https://app.example.com` for live app screenshots, or screenshots of the GitHub repo page are taken automatically.
