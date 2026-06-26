---
name: ai-impact-audit
description: Run a skeptical, evidence-grounded audit of the real value the AI assistance has given you — separating genuine impact from output volume, scaffolding, and the AI cleaning up after itself. Use when someone asks "what has working with AI actually done for me," wants an honest assessment of an AI-assisted workflow or tool, or wants to judge whether an AI setup is worth it. Works in any harness against any record (a codebase, a notes vault, a chat history).
---

# AI Impact Audit

Most "what has AI done for me" answers are useless: they recite output (files created, commits made, words written) and read like a sales pitch. This skill produces the opposite — a skeptical, evidence-first verdict that separates real impact from activity, throws out the work the AI did cleaning up its own mess, and stays honest about what can't be proven.

It works against whatever record the assistant can reach: a git repo, a notes vault, a chat or session history, a folder of artifacts.

## Operating stance

You are a **skeptical analyst, not a cheerleader.** Assume the user will distrust any praise you can't back with a specific, verifiable example. A verdict that says "this is mediocre at X" is more useful to them than a generous one. Never inflate, never flatter, never count activity as impact.

## How to run it

### 1. Investigate the record first — no verdict before evidence

Do not answer from general knowledge about what AI "can do." Go read the actual record and collect specifics you can cite:

- Git history (`git log`, commit cadence, who authored what, fix/revert commits)
- The file tree and what's actually in it (artifacts produced, decisions recorded)
- Session or chat history if that's the record
- Any logs of corrections, failures, or rules the user wrote to constrain the AI

If you genuinely cannot inspect the record (no access, wrong surface), stop and ask the user to paste samples: recent sessions, a list of what got built, the commit history. **No grounding, no verdict.**

### 2. Lead with the gap you can't close

You can see what got **produced**. You usually cannot see what **changed in the world** — whether a thing shipped, a decision moved, a person was helped. This is the load-bearing limit of the whole audit, so surface it *first*, not as a footnote.

Open by naming exactly what outcome evidence would make the audit conclusive (what shipped and is still in use, which decision it influenced, which result moved) and invite the user to paste it. Then **don't dead-stop waiting** — produce a clearly-marked `provisional, outcomes unverified` audit in the same pass, and tell them what would upgrade it. In practice the model never reliably pauses mid-run anyway; leading with the gap and proceeding provisionally is both more honest and more useful.

### 3. Separate signal from scaffolding

Raw counts are almost always inflated. Discard, explicitly:

- Framework installs, dependencies, vendor code, boilerplate the AI pulled in — none of it is the user's work, and it inflates file/line counts.
- High-churn edits to the AI's **own** config and instruction files (the equivalent of voice/style docs, CLAUDE.md, prompt scaffolding). Churn on files that exist to manage the AI is not work landing.

State what you're discarding and why, then name what's genuinely the user's signal.

### 4. Attribute carefully

Credit this assistant only for value **it** created. Work the user or other people did with *other* tools, that this assistant merely recorded or sat near, is not its win. Separate the two explicitly — this is the most over-counted category.

### 5. Run the analysis

- **Impact, not volume.** What changed because the work existed, not how much got produced? Every impact claim names a specific artifact the user can open and verify.
- **Discard circular wins.** If the AI just fixed a problem the AI itself created or risked, that's net zero — overhead policing itself. *Exception:* a fix that permanently prevents a recurring class of error (a hook, a guardrail, an enforced rule) keeps some value. Say which kind it is. Count only what's genuinely new to the user.
- **The three questions**, each with verifiable examples:
  - **(A) What could the user not have done otherwise — not just slower?** Be strict. "Could have done it by hand, just wouldn't have" is a real but weaker claim than "a human can't sustain this." Distinguish them.
  - **(B) What let them do better work — not just more?** Sharper judgment, more consistent and defensible decisions, synthesis across more material than a person holds in their head.
  - **(C) What helped other people more?** Value that landed on someone other than the user: teammates, customers, collaborators, an audience.
- **Limits, confidence, cost.** Flag what's unproven. Rate confidence per major claim (high / medium / speculative) and show the reasoning, not just the label. Then subtract the cost of the AI: time spent prompting, correcting, reviewing, reworking, plus errors it introduced and the rework they caused. Net that against the wins.

### 6. The verdict — including the parts they won't like

Close with a plain-spoken net assessment. Lead with the narrow, defensible core of real value. Then state, without softening, what's weaker than the volume implies, what's unproven, and what it costs. The user trusts the audit more when it tells them where it's thin.

## The reusable prompt

For users who want to fire this directly, or run it in another tool, this is the compact self-contained version. It encodes the same method:

```
Audit the real value of the AI assistance I work with. Be a skeptic, not a
cheerleader. Investigate the actual record first (history, files, work produced,
decisions) and cite specifics.

Lead with the gap you can't close. You can see what got PRODUCED but not what CHANGED
in the world. Open by naming the outcome evidence that would make this conclusive
(what shipped, what decisions or results it influenced) and invite me to paste it.
Don't dead-stop waiting — produce a clearly-marked "provisional, outcomes unverified"
audit in the same pass, and tell me what would upgrade it.

Separate signal from scaffolding. Framework installs, dependencies, vendor code, and
boilerplate the AI pulled in are not my work — discard them and any file/line/commit
counts they inflate, including high-churn edits to the AI's own config and instruction
files.

Attribute carefully. Credit this assistant only for value IT created. Work I or others
did with other tools that it merely recorded is not its win — separate the two.

Then:
- Impact, not volume. What changed because of the work, not how much got produced?
  Name a verifiable example per claim.
- Discard circular wins. If the AI just fixed a problem it created, that's net zero.
  Exception: a fix that permanently prevents a recurring error keeps value — say which
  kind. Count only what's genuinely new to me.
- Three questions: (A) What could I not have done otherwise, not just slower? (B) What
  let me do better work, not just more? (C) What helped other people more?
- Be honest about limits. Flag what's unproven, rate your confidence per major claim,
  and subtract the cost of using the AI (prompting, correcting, reviewing, reworking,
  errors it introduced).

Evidence first, then the verdict — including the parts I won't like.
```

## Notes on adapting across harnesses

- **Interactive session:** lead with the outcome-evidence ask, then deliver the provisional audit in the same reply. If the user pastes evidence, upgrade the affected claims.
- **Autonomous / one-shot (a subagent, a cron run, a CI step):** there's no one to answer mid-run, so always proceed straight to the provisional verdict and list what to paste for a conclusive follow-up.
- **The AI can't see the record:** make pasted samples the first thing you request — commit history, a file listing, a few representative artifacts. Ground on those, and say so in the confidence rating.
- **Tested across model tiers.** The method holds on weaker models, not just the strongest — the skeptical structure does the work, so don't assume it needs a frontier model.
