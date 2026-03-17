# Contributing to Claude Skills

This guide covers how we build skills in this repository. It's the single source of truth for conventions, patterns, and philosophy.

**Official Claude Code docs**: https://code.claude.com/docs/en/skills.md

## Philosophy

### Scripts first, markdown second

Put logic in executable scripts (`scripts/`), not in SKILL.md prose. SKILL.md is an orchestration layer — it tells Claude *what to run* and *when*, not *how the algorithm works*.

- Scripts are testable, debuggable, and deterministic
- Markdown instructions are ambiguous and produce variable results
- When Claude runs a script, the output is predictable
- Reserve detailed markdown for skills that are truly about Claude's reasoning (writing, analysis, code review)

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

All fields are optional except `description` (recommended).

#### Portable fields (work on Claude.ai and Claude Code)

| Field           | Description                                                    |
|:----------------|:---------------------------------------------------------------|
| `name`          | Lowercase, hyphens, max 64 chars. Defaults to directory name   |
| `description`   | What + when to use. Max 200 chars for Claude.ai                |
| `license`       | License identifier (e.g., `MIT`)                               |
| `allowed-tools` | Tools Claude can use without permission prompts                |
| `compatibility` | Platform compatibility info                                    |
| `metadata`      | Arbitrary key-value pairs                                      |

#### Claude Code-only fields

| Field                      | Description                                                           |
|:---------------------------|:----------------------------------------------------------------------|
| `disable-model-invocation` | `true` = only manual `/name` invocation. Use for side-effect skills   |
| `user-invocable`           | `false` = hidden from `/` menu, auto-loaded as background knowledge   |
| `model`                    | Pin a specific model when skill is active                             |
| `context`                  | `fork` = run in isolated subagent context                             |
| `agent`                    | Subagent type when `context: fork` (`Explore`, `Plan`, custom)        |
| `argument-hint`            | Autocomplete hint, e.g., `[issue-number]`                             |
| `hooks`                    | Hooks scoped to this skill's lifecycle                                |

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

Always use `uv` for Python virtual environments. Every skill with Python deps should have a `run.sh`:

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

### Plugin distribution

To share skills as a plugin:

1. Create `.claude-plugin/plugin.json` with name, description, version
2. Put skills in `skills/` directory at plugin root
3. Skills get namespaced: `/plugin-name:skill-name`
4. Test locally: `claude --plugin-dir ./my-plugin`

## Packaging for Claude.ai

Claude.ai has a **200 file limit** and **8MB size limit** for skill uploads.

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

## Conventions

### Naming
- Skill directories: lowercase with hyphens (`map-to-poster`, `disk-cleaner`)
- The `name` frontmatter field must match the directory name

### Description triggers
- Always include "Use when..." phrasing with specific keywords
- Write in third person: "Generates map posters from geographic coordinates"
- Keep under 200 chars for Claude.ai compatibility

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

- [Skills documentation](https://code.claude.com/docs/en/skills.md)
- [Sub-agents](https://code.claude.com/docs/en/sub-agents.md)
- [Plugins](https://code.claude.com/docs/en/plugins.md)
- [Hooks](https://code.claude.com/docs/en/hooks.md)
- [Agent Skills specification](https://agentskills.io)
