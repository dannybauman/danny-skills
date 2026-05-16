---
name: universal-agent-bridge
description: "Use this skill to convert proprietary IDE commands (like Claude Code custom slash commands) into cross-platform skills, commands, or MCP servers that work across Antigravity, Claude Code, and Cursor. Scaffold new standard workflows."
---

# Universal Agent Bridge

This skill helps developers and AI agents escape vendor lock-in by scaffolding standard, cross-platform agent capabilities. 

## The Golden Rule for Cross-Platform Agents
1. **Commands / MCP Servers (The Action Layer)**: If a task can be done deterministically without AI reasoning, make it an executable script or MCP server.
2. **Skills (The Reasoning Layer)**: If a task requires judgment or multi-step orchestration, define it as a `SKILL.md` that *uses* commands/tools.

When a user asks to migrate a custom proprietary slash command (e.g., from `.claude/config.json`), extract the deterministic logic into an executable command script, and create a `SKILL.md` to wrap it with reasoning and best practices.

## Usage

To scaffold a new cross-platform extension, run the python script using `uv run`. 

**Options:**
- `--type skill` (Creates a standard `SKILL.md` template)
- `--type command` (Creates a standard executable bash script template)
- `--type mcp` (Creates a FastMCP python server template)
- `--name <name>` (Name of the extension)
- `--dest <path>` (Destination directory for the new extension)

**Example:**
```bash
uv run /Users/Danny/Source/danny-skills/skills/universal-agent-bridge/scaffold_bridge.py --type skill --name "deploy-worker" --dest "./skills/deploy-worker"
```

## Steps for the Agent

1. Ask the user what kind of proprietary command or new workflow they want to build/convert.
2. Decide whether it needs to be an MCP server (data fetching/tooling), a Command (deterministic script), or a Skill (orchestration/SOP).
3. Determine the destination directory.
4. Execute the `scaffold_bridge.py` script with the correct arguments.
5. Review the generated files with the user and refine the logic.
