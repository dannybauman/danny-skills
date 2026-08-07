---
name: port-to-open-standard
description: "Use this skill to convert proprietary IDE commands (like Claude Code custom slash commands) into cross-platform skills, commands, or MCP servers that work across Antigravity, Claude Code, and Cursor. Scaffold new standard workflows."
---

# Port to Open Standard

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
uv run /Users/Danny/Source/danny-skills/skills/port-to-open-standard/scaffold_port.py --type skill --name "deploy-worker" --dest "./skills/deploy-worker"
```

## Porting Enforcement (hooks, permission gates, deny rules)

Enforcement is a third case, and the Golden Rule bends for it: the *deciding* logic must NOT be duplicated per platform. Port a **translator**, keep one authoritative gate.

0. **Rung zero — check for a native control before porting anything.** Most platforms already ship a declarative deny/allow layer (Antigravity: Settings → Permissions path rules; Claude Code: `permissions.deny`). A handful of native deny rules beats a ported adapter on every axis that matters — no subprocess, no payload-schema drift, survives your repo not being the workspace. Measured 2026-08-07: the ported hook adapter turned out to be dormant in the target IDE (hooks were a CLI-only feature there), while nine native deny rules added in the UI enforced immediately. The adapter below is the fallback for platforms with no native layer, and the probe (step 4) is what tells you which layer is actually live — wired and dormant look identical from the outside.

1. **One brain, thin adapters.** The platform-specific piece only converts payload shapes and verdict envelopes (e.g. Antigravity's `toolCall.args`/`{"decision": ...}` ↔ Claude Code's `tool_input`/`permissionDecision`). If the port contains a policy decision, it's wrong — push it down into the shared gate.
2. **The port may only narrow, never widen.** Its verdict vocabulary is deny-or-defer. Emitting "allow" from an adapter grants things the host platform might have asked about. Every failure path — bad JSON, wrong shape, subprocess crash, timeout — exits as an explicit deny, never a traceback (a crashed hook's effect is undefined on most platforms).
3. **Verify against the documented contract, not the implementation.** Build at least one fixture by hand FROM THE TARGET PLATFORM'S DOCS and pipe it into the real binary. A builder (human or agent) who writes both the code and its tests will make them agree with each other — all-green proves self-consistency, not correctness. Found live 2026-08-07: an agent invented a payload key ("arguments" vs the documented "args") and a hooks.json schema, and its 11 tests passed against both inventions.
4. **Ship a probe, not just tests.** Local tests prove the translator; only an in-situ probe (run the gated action inside the target platform, watch the deny fire) proves the wiring loaded. Write the probe prompt so it does NOT reveal the expected outcome — a model told "this should be denied" can role-play the denial without attempting the action. Re-run the probe after platform updates: they can silently unload hook config or add new tool names your matcher list has never heard of.
5. **Gate the wiring file itself.** The platform's hook-config file (e.g. `.agents/hooks.json`) is now part of your safety surface — add it to whatever change-control protects the rest.

Reference implementation: `roy` repo — `hooks/antigravity_gate_adapter.py` (translator), `.agents/hooks.json` (wiring), `docs/antigravity-gate-probe.md` (probe).

## Steps for the Agent

1. Ask the user what kind of proprietary command or new workflow they want to build/convert.
2. Decide whether it needs to be an MCP server (data fetching/tooling), a Command (deterministic script), or a Skill (orchestration/SOP).
3. Determine the destination directory.
4. Execute the `scaffold_port.py` script with the correct arguments.
5. Review the generated files with the user and refine the logic.
