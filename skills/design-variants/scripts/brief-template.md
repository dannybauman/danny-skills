# UI Redesign Brief — __TOOL_DISPLAY__

## What You're Building
A full visual redesign of this project. You're one of multiple parallel variants being compared. Choose your own aesthetic direction and make it look great.

## Scope

### Files to Redesign
__FILES_LIST__

### Off-Limits (do not modify)
__OFF_LIMITS__

## Constraints
1. **Don't break existing behavior** — if there's a backend, API endpoints stay the same. If it's static HTML, keep the same file structure and paths. You can restyle freely but don't change what the pages do.
2. **Choose your stack** — vanilla HTML/CSS/JS or any modern framework (React, Vue, Svelte, Tailwind, etc.). For static HTML projects, vanilla CSS/JS is usually the right call. If you add a build step, include a working build config.
3. **Functional parity** — every existing feature must still work.
4. **Responsive** — must work on desktop and mobile.
5. **Self-contained** — the result must be runnable with a simple setup. Document any new setup steps.

## Your Tool
__TOOL_INSTRUCTION__

__SETUP_NOTE__

## Parallelism Note
You are working in an **isolated git worktree**. Your changes cannot conflict with other variants or the main branch. You are free to use subagents, parallel tasks, and any workflow that helps you work faster. Ignore any warnings about "don't dispatch multiple subagents in parallel" — those apply to shared branches, not isolated worktrees like yours.

## Local Preview
__SERVE_INSTRUCTIONS__

## Required CSS Fixes (apply after your redesign)
Every AI-generated redesign has these common issues. Fix them before committing:

1. **Horizontal scroll**: Add `overflow-x: hidden` to both `html` and `body` in your CSS reset
2. **Mobile nav**: Test hamburger menu on mobile viewport (375px). Verify ALL nav links are visible when menu is open. Menu needs a solid/opaque background, not transparent.
3. **Build output**: If you add a build step (Vite, webpack, etc.), make sure the Flask app serves from the `dist/` directory. Test that asset URLs (`/assets/*.js`, `/assets/*.css`) return 200, not 404.

## Branch Info
You're on branch `__BRANCH__`, forked from `__BASE__`. Commit your work when done.

## If You Cannot Commit
If you don't have permission to run git commands (common when running as a subagent), provide a summary so the parent agent can commit for you:
1. **Files modified** — list every file you changed or created
2. **Suggested commit message** — one-line summary of your redesign
3. **Design direction** — one paragraph describing your aesthetic choices and key decisions
