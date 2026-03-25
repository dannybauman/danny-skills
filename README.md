# Danny's DS Skills

Claude Code [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) with work-related [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).

## Installation

Add the marketplace and install individual skills:

```bash
/plugin marketplace add dannybauman/danny-skills
/plugin install skill-name@danny-skills
```

Update all plugins to latest:

```bash
/plugin marketplace update danny-skills
```

Validate the marketplace locally:

```bash
claude plugin validate .
```

## Available Skills

| Skill | Description |
|:------|:------------|
| devseed-writing | Guide for writing and formatting blog posts and project pages for the Development Seed website |
| map-to-poster | Transforms cities into minimalist map posters from OpenStreetMap data |
| satellite-image | Fetch recent Sentinel-2 satellite imagery from Microsoft Planetary Computer |
| stac-scaffolder | Scaffolds a STAC (SpatioTemporal Asset Catalog) project using pystac |
| veda-story-creator | Generates VEDA scrollytelling story MDX files with satellite data visualizations |
| airtable | Interact with Airtable bases via the REST API — list, search, create, update records and manage attachments |

## Cross-Surface Compatibility

Skills in this marketplace are designed primarily for **Claude Code** (full network access, local package installation via `run.sh`). Skills can also be uploaded to **Claude.ai** via `package.sh` — note the 200-file / 8MB limit and that Claude.ai skills are per-user (not shared org-wide). The **Claude API** has no network access and no runtime package installation, so script-based skills won't work there without adaptation.

See the [official docs on where skills work](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#where-skills-work) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for skill authoring conventions.
