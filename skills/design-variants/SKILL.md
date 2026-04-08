---
name: design-variants
description: "Redesign a UI multiple ways at once using different AI tools, then compare. Triggers on: redesign, makeover, explore designs, try different styles, design options, make it look better, multiple versions, design shootout, UI refresh, visual overhaul."
---

## What This Does
Creates multiple parallel redesigns of a web project, each using a different AI design tool. Produces isolated git worktrees with briefs and ready-to-paste prompts for separate Claude Code sessions. Pairs with `/branch-compare` to view results side by side.

## How to Run

```
bash ${CLAUDE_SKILL_DIR}/run.sh $ARGUMENTS
```

Run with `--help` for all flags. No args = interactive guided mode. `--compare` auto-chains into branch-compare when variants are done.

## Detecting Where the User Is

Before doing anything, check the state of the repo. The user may not know what step they're at.

1. **No `design-variant-*` branches exist** → They haven't started. Run the full flow: scope → worktree → brief → prompts.
2. **`design-variant-*` branches exist but have no new commits beyond the fork point** → Worktrees were created but agents haven't done the work yet. Show the prompts again and explain what to do next.
3. **`design-variant-*` branches exist with new commits** → Work is done (or in progress). Run `/branch-compare design-variant-*` to show results. If some branches have commits and others don't, tell the user which ones are ready and which are still working.
4. **User has picked a winner** — they say "go with bmad" or "merge the stitch version" or "I like variant X":
   Run `bash ${CLAUDE_SKILL_DIR}/run.sh --pick <tool-name>` to merge the winner into main and clean up other worktrees.

Check with: `git branch --list 'design-variant-*'` and `git log main..design-variant-X --oneline`

## Adapting to the User

**If the user says something vague** like "redesign my UI", "make my app look better", "explore some design options":
1. Check state (above) to see if they already started
2. If fresh start: run the script with no args (guided mode)
3. Explain simply: "I'll create separate versions of your UI, each designed by a different AI tool. You'll be able to compare them side by side and pick your favorite."
4. After setup: "Open a new Claude Code window for each of these, paste the prompt, and let each one work. When they're done, come back and say 'compare the variants'."

**If the user knows what they want**: Run with tool names directly.

**If the user says "compare" or "show me the results"**: Skip this skill, go straight to `/branch-compare design-variant-*`.

## Cross-Skill Flow

These two skills are a pair. When the user's intent spans both:
- "Redesign my UI and show me the results" → run design-variants with `--compare` flag
- "Compare the variants" → run `/branch-compare design-variant-*` directly
- "Which version looks best?" → same as compare
- "Go with bmad" / "merge the bmad version" / "I pick X" → run with `--pick <tool-name>`

## Available Tools
Read from `${CLAUDE_SKILL_DIR}/scripts/tools.json`. Default: superpowers, frontend-design, bmad, stitch, gstack.

## Variant Dimensions

Variants can be created along different dimensions, not just tools:

- **Tools/frameworks**: Different AI design skills (superpowers, frontend-design, stitch, etc.)
- **Models**: Different AI models (Claude Opus 4.6, Sonnet 4.6, Gemini 3.1 Pro, GPT 5.4, etc.) — same prompt, different model generating the design
- **Prompts**: Same model, different design briefs (e.g. "minimal", "playful", "enterprise")

When the user asks to compare models, create one worktree per model. The brief stays the same but the prompt tells each session which model to use. For Claude models, use the `--model` flag. For non-Claude models, the brief should instruct the agent to use that model's API or tool.
