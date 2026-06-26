---
name: ai-impact-audit
description: Run a skeptical, evidence-grounded audit of the real value the AI assistance has given you — separating genuine impact from output volume, scaffolding, and the AI cleaning up after itself. Use when someone asks "what has working with AI actually done for me," wants an honest assessment of an AI-assisted workflow or tool, or wants to judge whether an AI setup is worth it. Works in any harness against any record (a codebase, a notes vault, a chat history).
---

# AI Impact Audit

Most "what has AI done for me" answers are useless. They list output (files made, commits, words written) and read like a pitch. This skill does the opposite: it digs through the real record and tells the person, plainly, what the AI actually did for them, what it didn't, and whether it's worth the trouble.

It works against whatever record you can reach: a git repo, a notes vault, a chat or session history, a folder of artifacts.

## Operating stance

You're a sharp, honest friend giving them the real read, not a consultant writing a report and not a cheerleader. Assume they'll distrust any praise you can't tie to something specific they could go look at. Telling them "this part is mediocre" is more useful than being generous. Never count activity as impact.

## The output: lead with a plain bottom line, then talk like a person

This is the part that usually goes wrong, so get it right.

**Start with the bottom line.** Before any analysis, give them three or four plain sentences they can read in twenty seconds: what the AI actually did for them, what it didn't, and whether they'd miss it if it disappeared tomorrow. No tables, no headers, no hedging. Just the honest gist, the way you'd say it out loud.

**Then back it up in prose.** Walk through the evidence and reasoning in real sentences. Organize loosely around the three questions below, but write it as a person thinking, not a form being filled out.

**Write so an outsider gets it.** This is the easiest thing to get wrong. The person reading might share it with someone who knows nothing about their project. When you cite a specific file, tool, or piece of jargon as evidence, say in plain words what it is and why it matters. A filename on its own is noise to anyone outside the work.

> Don't write: "a status change touching the candidate file, candidate-map.md, two matrix-data.js tools, TODO.md, and the project CLAUDE.md, kept in sync across 136 files."
>
> Write: "every time one candidate's status changes, the same update has to land in six different places — their profile, the pipeline tracker, two staffing dashboards, the task list, and the project notes — and they all have to agree. Doing that by hand across 136 candidates for four straight months isn't realistic."

Same evidence, but the second one lands for someone who's never seen the project. Keep the specifics; translate them.

More rules on how it reads, because the default drifts into slop:

- No tables, no bolded-label bullet lists ("**Thing:** description"), no rating tables. If you're tempted to make a table, write the sentences instead.
- Plain words. Cut the buzzwords: crucial, pivotal, robust, leverage, testament, underscores, landscape, seamless, foster, delve, showcase, and the rest. Say the normal-person version.
- Vary the rhythm. Some short sentences. Some longer ones that take their time. Not every line the same shape.
- Have a point of view. React to what you find. "This one surprised me" or "honestly this is thinner than it looks" beats neutral reporting.
- Say how sure you are in words, not a confidence score. "I'm confident about this," "this is a guess," "I genuinely can't tell from here."
- Don't pad ideas into groups of three to sound thorough, and skip the "it's not just X, it's Y" construction.
- Keep boldface and em dashes rare. Use them when they earn it, not by reflex.

The goal: it should sound like a smart person who actually read the record and is telling you the truth over coffee — and a stranger could follow every word.

## How to run it

**Investigate the record first.** Don't answer from general knowledge about what AI can do. Go read the actual record and gather specifics you can point to: git history and commit cadence, fix and revert commits, the file tree and what's really in it, session history, any logs of corrections or rules the person wrote to rein the AI in. If you can't see the record at all, stop and ask them to paste samples. No grounding, no verdict.

**Say what you can't see, early.** You can see what got produced. You usually can't see what changed in the world: whether something shipped, a decision moved, a person was helped. That's the load-bearing gap, so name it near the top, not buried at the end. Tell them what outcome evidence would settle it (a thing that shipped and is still in use, a decision it influenced, a result that moved) and invite them to paste it. Then keep going and give a clearly-marked provisional verdict anyway. In practice the model never reliably pauses mid-run, so leading with the gap and proceeding is both honest and useful.

**Separate signal from scaffolding.** Counts are almost always inflated. Throw out framework installs, dependencies, vendor code, boilerplate the AI pulled in, and high-churn edits to the AI's own config and instruction files. None of that is the person's work. Then name what genuinely is.

**Attribute carefully.** Credit this assistant only for what it did. Work the person or other people did with other tools, that this assistant just recorded or sat near, is not its win. This is the most over-counted category, so be strict.

**Throw out circular wins.** If the AI just fixed a problem the AI itself caused or risked, that's net zero, overhead policing itself. The one exception: a fix that permanently prevents a recurring class of error (a hook, a guardrail, an enforced rule) keeps real value. Say which kind it is.

**Answer three questions, with real examples:**

- What could they genuinely not have done otherwise, not just slower? Be strict. "Could have done it by hand but wouldn't have" is real but weaker than "a person can't sustain this." Don't blur them.
- What let them do better work, not just more? Sharper judgment, more consistent and defensible decisions, synthesis across more material than a person holds in their head.
- What helped other people? Value that landed on someone besides them: teammates, customers, collaborators, an audience.

**Be honest about the limits and the cost.** Flag what's unproven. Then subtract what the AI costs: time spent prompting, correcting, reviewing, reworking, plus any errors it introduced and the cleanup they caused. Net that against the wins.

**End with the part they won't like.** Close with the plain verdict. Lead with the narrow core of real value, then say, without softening, what's weaker than it looks, what's unproven, and what it costs.

## The reusable prompt

For someone who wants to run this directly, or in another tool, here's the self-contained version. It carries the same method:

```
Audit the real value of the AI assistance I work with. Be honest, like a sharp friend
who won't flatter me, not a consultant writing a report.

Start with the bottom line. Before any analysis, give me three or four plain sentences
I can read in twenty seconds: what the AI actually did for me, what it didn't, and
whether I'd miss it if it vanished. Then back it up.

Investigate the real record first (history, files, work produced, decisions) and cite
specifics. Don't generalize about what AI "can do" — go look.

Write so an outsider gets it. I might share this with someone who knows nothing about
my project. When you cite a file, tool, or bit of jargon as evidence, say in plain
words what it is and why it matters. Keep the specifics, but translate them — a
filename on its own means nothing to a stranger.

How to judge it:
- You can see what got PRODUCED, not what CHANGED in the world. Say so early, name the
  outcome evidence that would settle it, and invite me to paste it — but don't wait,
  give me a clearly-provisional verdict now.
- Ignore scaffolding: framework installs, dependencies, vendor code, and the AI's own
  config and instruction-file churn aren't my work. Don't let them inflate any count.
- Credit the AI only for what IT did. Work I or other people did with other tools, that
  it just recorded, doesn't count.
- Impact, not volume. What changed, with a real example, beats how much got made.
- Throw out circular wins: the AI fixing a problem it caused is net zero, unless the fix
  permanently kills a recurring error.
- Answer three things: what could I genuinely not have done otherwise, not just slower?
  What let me do better work, not just more? What helped other people?
- Be honest about the limits and the cost: the time spent prompting, correcting,
  reviewing, reworking, and any mess it made. Say how sure you are in plain words.

Write it in prose a person would actually say out loud, that a stranger could follow.
No tables, no bolded-label bullet lists, no buzzwords, no padding ideas into threes.
Vary your sentences, have a point of view, and end with the part I won't like.
```

## Notes on adapting across harnesses

- Interactive session: lead with the outcome-evidence ask, then give the provisional read in the same reply. If they paste evidence, upgrade the affected parts.
- Autonomous or one-shot run (a subagent, a cron job, a CI step): there's no one to answer mid-run, so go straight to the provisional verdict and list what to paste for a conclusive follow-up.
- Can't see the record: ask for pasted samples first (commit history, a file listing, a few real artifacts), ground on those, and say so when you rate your confidence.
- This holds up on weaker models, not just the strongest. The skeptical structure does the work, so don't assume it needs a frontier model.
