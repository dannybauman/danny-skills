# CLAUDE.md

## Git

This repo is owned by `dannybauman`. **Always** use the dannybauman GitHub account for all git operations — commits and pushes.

Before any git push:

```bash
unset GH_TOKEN && gh auth switch --user dannybauman
```

The `unset GH_TOKEN` is required because a shell-level token overrides `gh auth switch`. Other GitHub accounts will get 403 errors on this repo.

Never commit as another user. If you see a non-dannybauman commit, rewrite it with `git filter-branch` or `git rebase`.

## Philosophy

- **Deterministic scripts over markdown** — put logic in executable code, not LLM instructions
- **uv first** — always prefer uv for Python venvs and deps
- **Reuse code** — extract common patterns, don't reimplement
