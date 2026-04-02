# Contributing to Claude Skills

This guide covers how we build skills in this repository. It's the single source of truth for conventions, patterns, and philosophy.

**Official docs**:
- [Skills in Claude Code](https://code.claude.com/docs/en/skills)
- [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)

## Philosophy

### Deterministic scripts over markdown

Do as much as possible in executable scripts and code, not markdown instructions for language models. The more a skill can do without Claude's judgment, the more reliable it is.

- Scripts are testable, debuggable, and deterministic
- Markdown instructions are ambiguous and produce variable results
- When Claude runs a script, the output is predictable
- SKILL.md is an orchestration layer — it tells Claude *what to run* and *when*, not *how the algorithm works*
- Reserve detailed markdown only for skills that are truly about Claude's reasoning (writing, analysis, code review)

### Reuse code well

Extract common patterns and share them between skills rather than reimplementing.

- Check existing skills for reusable helpers before writing new code
- Shared rendering utilities, CLI patterns, and I/O conventions should be consistent
- Reference working implementations rather than writing from scratch
- If a pattern works in one skill, extract it so other skills can use it

### Use `/skill-creator` for new skills

The `/skill-creator` skill provides a structured development lifecycle:

1. Capture intent and requirements
2. Write the initial skill draft
3. Create test cases and run evaluations
4. Review and grade results
5. Iterate based on feedback
6. Optimize the description for triggering accuracy

Run `/skill-creator` in Claude Code to get started.

### Keep it lean

- SKILL.md under 500 lines
- Only add context Claude doesn't already have
- Move detailed reference material to supporting files
- Claude loads supporting files on demand, not upfront

## Skill Structure

```
skill-name/
├── SKILL.md              # Required: frontmatter + orchestration instructions
├── run.sh                # Recommended: single entrypoint, handles deps
├── requirements.txt      # Python dependencies (if applicable)
├── scripts/              # The real logic lives here
├── resources/            # Templates, reference docs, examples
├── input/                # User-provided files (gitignored)
└── output/               # Generated artifacts (gitignored)
```

### SKILL.md Frontmatter

All fields are optional except `description` (recommended). Only `name` and `description` are recognized across all surfaces (Claude Code, Claude.ai, Claude API).

#### Field reference

| Field                      | Surface      | Description                                                           |
|:---------------------------|:-------------|:----------------------------------------------------------------------|
| `name`                     | All          | Lowercase letters, numbers, hyphens only. Max 64 chars. No reserved words (`anthropic`, `claude`). No XML tags. Defaults to directory name |
| `description`              | All          | What + when to use. Max 1024 chars. No XML tags. Write in **third person** ("Generates...", not "I can help you...") |
| `allowed-tools`            | All          | Tools Claude can use without permission prompts when skill is active  |
| `disable-model-invocation` | Claude Code  | `true` = only manual `/name` invocation. Use for side-effect skills   |
| `user-invocable`           | Claude Code  | `false` = hidden from `/` menu, auto-loaded as background knowledge   |
| `model`                    | Claude Code  | Pin a specific model when skill is active                             |
| `effort`                   | Claude Code  | Effort level override: `low`, `medium`, `high`, `max` (Opus 4.6 only) |
| `context`                  | Claude Code  | `fork` = run in isolated subagent context                             |
| `agent`                    | Claude Code  | Subagent type when `context: fork` (`Explore`, `Plan`, `general-purpose`, or custom) |
| `argument-hint`            | Claude Code  | Autocomplete hint, e.g., `[issue-number]`                             |
| `hooks`                    | Claude Code  | Hooks scoped to this skill's lifecycle                                |

**Do not include Claude Code-only fields** in skills you plan to upload to Claude.ai — they cause upload errors.

### String Substitutions

| Variable               | Description                                       |
|:-----------------------|:--------------------------------------------------|
| `$ARGUMENTS`           | All arguments passed when invoking                |
| `$ARGUMENTS[N]` / `$N`| Specific argument by 0-based index                |
| `${CLAUDE_SESSION_ID}` | Current session ID                                |
| `${CLAUDE_SKILL_DIR}`  | Directory containing the skill's SKILL.md         |

### Dynamic Context Injection

Use `` !`command` `` in SKILL.md to run shell commands before Claude sees the content:

```markdown
## Context
- Branch: !`git branch --show-current`
- Changed files: !`git diff --name-only`
```

The command output replaces the placeholder. This is preprocessing, not something Claude executes.

## run.sh Pattern

Always use `uv` for Python virtual environments — it's faster, cleaner, and the default toolchain. Fall back to standard `venv`/`pip` only for portability. Every skill with Python deps should have a `run.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if command -v uv &> /dev/null; then
    if [ ! -d ".venv" ]; then
        uv venv .venv
    fi
    if [ -f "requirements.txt" ]; then
        uv pip install -r requirements.txt
    fi
    PYTHON=".venv/bin/python"
else
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    PYTHON=".venv/bin/python"
fi

$PYTHON scripts/main.py "$@"
```

Key points:
- `set -euo pipefail` — fail fast on errors
- `cd "$(dirname "$0")"` — always run from skill directory
- `uv` preferred, standard `venv` as fallback
- Pass all arguments through with `"$@"`

## Supporting Files (Subskills)

When a skill gets complex, break it into supporting files rather than bloating SKILL.md:

```
my-skill/
├── SKILL.md           # Overview + navigation (under 500 lines)
├── reference.md       # Detailed API docs (loaded on demand)
├── examples.md        # Usage examples (loaded on demand)
└── scripts/
    └── helper.py      # Executed, not loaded into context
```

Reference them from SKILL.md so Claude knows they exist:

```markdown
## Additional resources
- For complete API details, see [reference.md](reference.md)
- For usage examples, see [examples.md](examples.md)
```

Claude loads these only when needed, saving context window space.

## Progressive Disclosure

Skills load in three levels — only what's needed enters the context window:

| Level | When Loaded | Token Cost | Content |
|:------|:------------|:-----------|:--------|
| **Metadata** | Always (at startup) | ~100 tokens | `name` and `description` from frontmatter |
| **Instructions** | When skill is triggered | Under 5k tokens | SKILL.md body |
| **Resources** | As needed | Effectively unlimited | Supporting files, scripts (executed, not loaded) |

This means you can bundle extensive reference material without context penalty — Claude reads it only when needed. Keep SKILL.md under 500 lines and push detailed docs to supporting files.

## Descriptions & Triggering

The `description` field is how Claude decides whether to use your skill. Write it carefully:

- **Third person**: "Generates map posters..." not "I can help you..."
- **Include "Use when..."**: with specific keywords users would naturally say
- **Be specific**: "Extract text and tables from PDF files, fill forms, merge documents" not "Helps with documents"
- **Max 1024 chars** (keep under 200 chars if you want Claude.ai compatibility)
- **No XML tags** in the description

## Degrees of Freedom

Match instruction specificity to how fragile the task is:

- **High freedom** (text instructions, multiple approaches valid): code review, writing, analysis
- **Medium freedom** (pseudocode/scripts with parameters): report generation, scaffolding
- **Low freedom** (exact scripts, no variation): database migrations, deployments, API calls with fragile sequences

Default to high freedom. Only constrain when consistency or correctness requires it.

## Feedback Loops

For quality-critical skills, build in validation steps:

```
1. Generate output
2. Validate (run script or check against rules)
3. If errors → fix and re-validate
4. Only proceed when validation passes
```

This pattern dramatically improves output quality, especially for skills that modify files or generate structured output.

## Advanced Patterns

### Running skills in a subagent

Add `context: fork` to isolate a skill from the main conversation:

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---

Research $ARGUMENTS thoroughly:
1. Find relevant files using Glob and Grep
2. Read and analyze the code
3. Summarize findings with specific file references
```

Agent options: `Explore` (read-only, fast/Haiku), `Plan` (read-only, inherits model), `general-purpose` (all tools), or custom agents from `.claude/agents/`.

### Hooks in skills

Scope hooks to a skill's lifecycle:

```yaml
---
name: secure-ops
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate.sh"
---
```

### Plugin marketplace distribution

This repo is a plugin marketplace. The `.claude-plugin/marketplace.json` at the root defines all available plugins. Each plugin entry needs `name`, `source`, and `description`.

**Plugin sources** (in `marketplace.json`):
- **Relative path**: `"source": "./skills/my-skill"` — plugin lives in this repo
- **GitHub**: `"source": {"source": "github", "repo": "owner/repo", "ref": "v1.0"}`
- **Git URL**: `"source": {"source": "url", "url": "https://gitlab.com/team/plugin.git"}`
- **Git subdirectory**: `"source": {"source": "git-subdir", "url": "...", "path": "tools/plugin"}`
- **npm**: `"source": {"source": "npm", "package": "@scope/plugin", "version": "^2.0"}`

**Validation**: Run `claude plugin validate .` or `/plugin validate .` before pushing.

**Updating**: Users pull updates with `/plugin marketplace update danny-skills`.

**For private repos**: Background auto-updates need `GITHUB_TOKEN` or `GH_TOKEN` set in the shell environment. Manual install/update uses existing git credential helpers.

## Cross-Surface Packaging

### Claude.ai

Claude.ai has a **200 file limit** and **8MB size limit** for skill uploads. Use `package.sh`:

```bash
./package.sh skill-name
```

Or manually:

```bash
zip -r skill-name.zip skill-name/ \
  -x "*/.venv/*" "*/output/*" "*/input/*" "*/.env" \
  "*/__pycache__/*" "*/.DS_Store" "*/node_modules/*" \
  "*/.git/*" "*/deps/*"
```

Always verify before upload:

```bash
zipinfo -1 skill-name.zip | wc -l  # Must be < 200
```

**Note**: Claude.ai skills are per-user — each team member must upload separately. Skills uploaded to Claude.ai are NOT available via the API or Claude Code (and vice versa).

### Claude API

Custom skills can be uploaded to the API via `POST /v1/skills` (beta). API skills are workspace-wide. The API has **no network access** and **no runtime package installation**, so script-based skills that use `run.sh` won't work without adaptation. See the [API skills guide](https://platform.claude.com/docs/en/build-with-claude/skills-guide).

### Claude Code (this marketplace)

Skills are installed via the plugin marketplace and have full network access and local package installation. This is the primary target for skills in this repo.

## Testing

- **Test with real tasks**, not contrived scenarios
- **Test across models** if the skill may be used with different models (Haiku needs more guidance, Opus needs less)
- **Evaluation-driven development**: Run Claude on representative tasks *without* the skill first, document failures, then write just enough to fix those gaps
- **Observe how Claude navigates**: Watch which files it reads, in what order. If it misses references or overuses one file, restructure

## Anti-Patterns

- **Deeply nested references**: Keep file references one level deep from SKILL.md. Claude may partially read files referenced from *other* referenced files
- **Too many options**: Don't list 5 libraries — pick one default with an escape hatch for edge cases
- **Windows-style paths**: Always use forward slashes (`scripts/helper.py`), even if developing on Windows
- **Time-sensitive info**: Don't write "before August 2025, use the old API." Put deprecated patterns in a collapsible "Old patterns" section
- **Inconsistent terminology**: Pick one term and stick with it (e.g., always "field", not sometimes "box" or "element")
- **Over-explaining what Claude already knows**: Challenge every paragraph — does Claude really need this?

## Conventions

### Naming
- Skill directories: lowercase letters, numbers, hyphens only (`map-to-poster`, `satellite-image`)
- Max 64 characters, no reserved words (`anthropic`, `claude`)
- The `name` frontmatter field must match the directory name
- Consider **gerund form** for clarity: `processing-pdfs`, `analyzing-data`
- Avoid vague names: `helper`, `utils`, `tools`

### Description triggers
- Always include "Use when..." phrasing with specific keywords
- Write in third person: "Generates map posters from geographic coordinates"
- Be specific: include concrete nouns and verbs users would say
- Keep under 200 chars for Claude.ai compatibility (max 1024 chars for Claude Code)

### I/O discipline
- User-provided files go in `input/`
- Generated artifacts go in `output/`
- Both directories are gitignored

### Resource consent
- If a skill requires downloads >500MB or long operations, calculate and confirm with user first
- Support `--yes` or `--force` flag for automation

### Dependencies
- Python packages: `requirements.txt` + `.venv` via `run.sh`
- Git-cloned repos: `deps/` subdirectory (gitignored)
- Node packages: `node_modules/` (gitignored)

### Side-effect safety
- Add `disable-model-invocation: true` to skills that deploy, push, or modify external state
- This prevents Claude from auto-triggering dangerous operations

## Where Skills Live

| Location   | Path                                     | Scope                 |
|:-----------|:-----------------------------------------|:----------------------|
| Enterprise | Managed settings                         | All users in org      |
| Personal   | `~/.claude/skills/<name>/SKILL.md`       | All your projects     |
| Project    | `.claude/skills/<name>/SKILL.md`         | This project only     |
| Plugin     | `<plugin>/skills/<name>/SKILL.md`        | Where plugin enabled  |

Priority: enterprise > personal > project. Plugin skills use namespace `plugin-name:skill-name`.

This repo contains **standalone portable skills** — copy any skill folder to your personal or project skills directory to use it.

## Official References

- [Skills in Claude Code](https://code.claude.com/docs/en/skills)
- [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Skills API guide](https://platform.claude.com/docs/en/build-with-claude/skills-guide)
- [Sub-agents](https://code.claude.com/docs/en/sub-agents)
- [Plugins](https://code.claude.com/docs/en/plugins)
- [Hooks](https://code.claude.com/docs/en/hooks)
- [Agent Skills specification](https://agentskills.io)
