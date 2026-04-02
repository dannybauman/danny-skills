# Project Video Workflow

## Step-by-step

1. **Accept input** — User provides a GitHub repo URL (required) and optionally a deployed app URL.

2. **Research the project** — Run `research_project.py` which uses `gh` CLI and code analysis to gather:
   - Repo name, description, topics, stars, forks
   - Language breakdown and tech stack (from manifests)
   - Directory structure overview
   - README summary
   - Recent notable PRs/commits
   - Contributor count
   - Deployed URL (detected from README if not provided)

3. **Propose narrative** — Based on research, propose a scene sequence. Ask the user:
   - "What's the key feature to highlight?" (if not obvious from README)
   - "Is there a live URL?" (if not detected)

4. **Take screenshots** (optional) — If a URL is available and Playwright is installed:
   - Screenshot the deployed app
   - Screenshot the GitHub repo page
   - Save to `screenshots/` directory

5. **Generate scene PNGs** — Pillow renders each scene as a 1920x1080 PNG:
   - Title/hook card (project name + one-liner)
   - Problem/context card
   - Tech stack card
   - Architecture overview
   - 2-4 feature cards (with screenshot insets if available)
   - Live demo card (if screenshot available)
   - Stats card (contributors, commits, stars, LOC)
   - Closing card (repo URL + install command)

6. **Assemble video** — FFmpeg chains scenes with xfade transitions into a single MP4.

7. **Open result** — Report the file path and open with system viewer.

## Tips

- Use `--dry-run` to preview scene PNGs before committing to the full video
- Use `--theme` to match the project's aesthetic
- The research JSON can be edited manually for custom narratives
- Screenshots are always optional — the video works without them
