# CLAUDE.md

## Git

Before any git push, switch to the `dannybauman` GitHub account:

```bash
unset GH_TOKEN && gh auth switch --user dannybauman
```

The repo is owned by `dannybauman`. Other accounts (goggledefogger, hypepirate) will get 403 errors.

## Philosophy

- **Deterministic scripts over markdown** — put logic in executable code, not LLM instructions
- **uv first** — always prefer uv for Python venvs and deps
- **Reuse code** — extract common patterns, don't reimplement
