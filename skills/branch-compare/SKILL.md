---
name: branch-compare
description: "Compare git branches visually side by side. Triggers on: compare branches, show me the versions, which design is better, compare variants, see the differences, side by side, visual diff, before and after."
---

## What This Does
Compares git branches by serving each on its own localhost port and opening a tabbed switcher UI in the browser. Works with any web project.

## How to Run

```
bash ${CLAUDE_SKILL_DIR}/run.sh $ARGUMENTS
```

Run with `--help` for all flags. `--wait` polls for new commits before comparing (useful after `/design-variants`).

## Detecting Where the User Is

Before doing anything, check what exists:

1. **`design-variant-*` branches exist** → The user probably used `/design-variants`. Run with `design-variant-*` automatically.
2. **Other non-main branches exist** → Ask which ones to compare, or compare all recent ones.
3. **No branches to compare** → Explain the tool and suggest `/design-variants` to create variants, or `git checkout -b` to create branches manually.
4. **Servers already running** (check `.state/pids/`) → The switcher is probably already open. Tell the user to refresh their browser, or offer to restart with updated branches.

## Adapting to the User

**If the user says something vague** like "compare my branches", "show me the different versions", "which one looks best", "let me see them":
1. Check state (above) — auto-detect the right branches
2. If `design-variant-*` branches exist, use those without asking
3. Run and open the switcher

**If the user is specific**: Run with those branch names directly.

**If API calls fail** (loading spinners, "failed to load" errors):
Backend URLs probably point to Docker-internal or production hosts. Help the user create a `.branch-compare.env` in the repo root with correct local URLs, then restart.

**If the user picks a winner** ("I like this one", "go with bmad", "merge this version"):
Hand off to `/design-variants --pick <tool-name>`. Don't try to merge yourself.

**To stop:** `--stop`. To also clean up worktrees: `--stop --cleanup`.

## Cross-Skill Flow

If the user wants to create design variants (not just compare existing branches), suggest `/design-variants`. Don't make them figure out the two-skill relationship — if they say "redesign my app in different styles" and no variant branches exist, hand off to `/design-variants`.
