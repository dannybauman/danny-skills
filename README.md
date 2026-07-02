# danny-skills

Skills I've built for [Claude Code](https://code.claude.com/docs/en/plugin-marketplaces). Mostly stuff that came out of real work — geo/satellite tools, content pipelines, design workflows. Some are polished, some are scrappy.

## Install

```bash
/plugin marketplace add dannybauman/danny-skills
/plugin install skill-name@danny-skills
```

Update everything:

```bash
/plugin marketplace update danny-skills
```

## Skills

| Skill | What it does |
|:------|:------------|
| ai-impact-audit | Skeptically audit the real value AI assistance has given you, separating impact from volume, scaffolding, and self-cleanup |
| airtable | Talk to Airtable bases — list, search, create, update records and manage attachments |
| branch-compare | Compare git branches visually side by side with a hot-swappable browser preview |
| design-variants | Redesign a UI multiple ways at once using different AI tools, then compare them |
| devseed-writing | Write and format blog posts and project pages for the Dev Seed website |
| map-to-poster | Turn cities into minimalist map posters from OpenStreetMap data |
| port-to-open-standard | Scaffold cross-platform agent skills, commands, and MCP servers to escape vendor lock-in |
| project-video | Generate short highlight reel videos for software projects |
| satellite-image | Pull recent Sentinel-2 imagery from Microsoft Planetary Computer |
| slack-to-markdown | Grab a Slack thread from a URL and save it as clean Markdown |
| integrating-local-models | Wire a local LLM or audio model into an app or agent, with capability probes that catch the tool-calling trap |
| stac-scaffolder | Scaffold a STAC (SpatioTemporal Asset Catalog) project with pystac |
| veda-story-creator | Generate VEDA scrollytelling story MDX files with satellite data visualizations |

## Good to know

These are built for **Claude Code** — they assume local network access and can install their own deps via `run.sh`. You can also zip them up for **Claude.ai** (`package.sh`), but that surface has a 200-file / 8MB limit and skills are per-user. The **Claude API** has no network access, so the script-heavy ones won't work there without rework.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
