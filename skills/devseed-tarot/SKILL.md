---
name: devseed-tarot
description: Draws a fun, DevSeed-flavored tarot reading from any git repo, project, or vault — no topic needed (it reads recent commit activity for grounding) or with a question/topic as the lens. Renders as a small, on-brand local web page (opens on localhost), with a toggle between a generic "DevSeed" reading and one grounded in this specific project's real signal. Use when someone asks for "a tarot reading," "/devseed-tarot," "read this repo's tarot," or wants a fun, insightful gut-check on a project. Portable — works in any repo, degrades gracefully without git, never names individuals.
---

# DevSeed Tarot — The Basemap Deck

A tarot reading, reskinned: 22 cards themed on dev/open-source/consulting
culture instead of swords and cups, drawn against whatever repo you run it
in. Every card is illustrated as a chart fragment in a wayfinding visual
language drawn from the world's charting traditions (see
`references/icons/README.md`) — the reading is a small act of navigation,
and the whole experience speaks that way, from welcome message to page. No
server-side app, no dependencies beyond what's already on the machine —
Claude does the reading, a static page shows it.

## When this triggers

"Give me a tarot reading," "/devseed-tarot," "do my tarot cards," "read this
repo's tarot," "tarot reading for [topic/question]," or general requests for
a fun pattern-matching gut-check on a project's recent state.

The optional argument is a **topic or question** ("should we take on this
contract," "how's this refactor going," "what's next for this pod's tooling")
— not a theme choice. Theme is handled by a toggle in the page itself (see
below), not a flag.

## Step 0 — welcome before you do anything

Before running any commands, send a short (2–4 sentence) heads-up in chat.
Plain voice with a light wayfinding touch — no mysticism, no over-explaining.
Something like:

> Charting a reading — I'll fix your position from [this repo's recent
> activity / your question] and draw four cards from the Basemap Deck:
> where you sailed from, where you are, what's on the horizon, and a star
> to steer by. It'll open as a small page in your browser in a few seconds.
> Nothing personal or sensitive goes in it — just patterns, no names.

This matters because first-time users have no idea what's about to happen or
that a browser tab is coming. The four-position preview doubles as the
explanation of how to read the spread.

## Step 1 — figure out the lens for content (not the visual theme)

- **Topic/question given** → that's the primary lens. Everything below still
  happens, but the interpretation leans on the question, not on digging
  through history.
- **No topic** → ground it in the target repo's recent activity (Step 2).

## Step 2 — gather grounding signal (shallow, safe, fast)

Run these from the target repo's root (default: current working directory,
or wherever the user points you).

**If it's a git repo** (`git rev-parse --is-inside-work-tree` succeeds):
```
git log --since="30 days ago" --pretty=format:"%s"
```
If that returns fewer than ~8 lines, widen the window (90 days, then
`-n 60` with no date bound at all). Subjects only — never pull diffs, bodies,
or author names into the reading.

**If it's not a git repo**, fall back to a shallow structural scan:
`find . -maxdepth 2 -not -path '*/.git/*' | head -60` or `ls -lt` on the top
two levels, for a rough sense of what's active/large/recent.

**Either way, grab a few light repo facts** for the "this project" lens:
- Project name: repo folder name, or README's first heading
- One-line description: README's first paragraph, or a `description` field
  in `package.json`/`pyproject.toml`/similar, if present
- Rough stack: whichever manifest exists (`package.json`, `pyproject.toml`,
  `Cargo.toml`, `go.mod`, `Gemfile`, `requirements.txt`, ...) tells you the
  language/ecosystem

Keep this shallow — subjects and filenames, not deep reads of file content.
This skill runs in other people's repos; treat everything it touches as
possibly sensitive even if it usually isn't.

## Step 3 — draw 4 cards

The deck (22 cards, names + meanings) lives in `references/deck.md`. Draw 4
unique cards without replacement:

```
shuf -i 0-21 -n 4 2>/dev/null || python3 -c "import random; print(*random.sample(range(22),4))"
```

Map the 4 numbers to this index — name and icon filename both live in
`references/icons/` under the same index (matches `references/deck.md`
order exactly):

```
0  THE GREENFIELD          00-greenfield.svg
1  THE OPEN SOURCE COMMIT  01-open-source-commit.svg
2  THE STAC CATALOG        02-stac-catalog.svg
3  THE DATA PIPELINE       03-data-pipeline.svg
4  THE LEGACY SYSTEM       04-legacy-system.svg
5  THE FORK                05-fork.svg
6  THE POD                 06-pod.svg
7  THE SPRINT              07-sprint.svg
8  THE COG                 08-cog.svg
9  THE ASYNC HANDOFF       09-async-handoff.svg
10 THE SCOPE CREEP         10-scope-creep.svg
11 THE MERGE CONFLICT      11-merge-conflict.svg
12 THE OPEN PR             12-open-pr.svg
13 THE POSTMORTEM          13-postmortem.svg
14 THE REBASE              14-rebase.svg
15 THE WILDCARD TICKET     15-wildcard-ticket.svg
16 THE OUTAGE              16-outage.svg
17 THE DASHBOARD           17-dashboard.svg
18 THE RETRO               18-retro.svg
19 THE BIG TENT            19-big-tent.svg
20 THE TEAM WEEK           20-team-week.svg
21 THE RELEASE             21-release.svg
```

Card names, icons, and spread positions are fixed (like a real deck, they
don't get renamed per project) — only the interpretation text varies. The 4
positions, in order: **Departure** (recent past — where you sailed from) →
**Present Position** (now) → **On the Horizon** (near future) → **The
Steering Star** (guidance).

The icon set is a swappable, external asset — see
`references/icons/README.md` before assuming it's fixed. Someone can drop in
a different icon library or hand-drawn set (same 22 filenames) without
touching this skill or the template.

## Step 4 — write the reading (two lenses per card)

For each of the 4 drawn cards, write two short takes (2–3 sentences each),
starting from that card's base meaning in `references/deck.md`:

- **DevSeed lens** — generic, safe, dev-culture framing. Tied to the
  question or the general shape of recent activity, but no repo-specific
  facts. This is the one anyone could screenshot without a second thought.
- **Project lens** — same card, same position, but grounded in what you
  actually found in Step 2 (real commit themes, the stack, the shape of the
  work). More specific, still never naming a teammate, a candidate, or
  quoting private content — describe *work and patterns*, not *people*.

### Tone and boundaries

Mild, dry, mostly positive — never cheesy, never sarcastic at anyone's
expense. Consulting work has real texture: partners and clients with
different paces, asks that shift mid-flight, data that wasn't quite ready
when promised. It's fine for a reading to gesture at that lightly, especially
through cards built for exactly this (The Scope Creep, The Wildcard Ticket,
The Async Handoff, The Outage). The stance is always self-deprecating about
*our own* delivery, never mocking a partner.

If the repo clearly belongs to a named partner or program (a name in the
README, a folder name, a remote), it's fine to name them once, warmly —
something like "coordinating with a space agency's timeline has its own
gravity" reads fine either way: funny if you were there, unremarkable if you
weren't. One aside like this per reading, max. Never air anything that would
embarrass anyone if screenshotted. Never invent a partner that isn't
actually evident in the repo.

## Step 5 — render and serve

1. Read `references/template.html`, replace every `{{TOKEN}}` with the real
   content (subject, grounding line, date, and each card's numeral / name /
   keyword / icon filename / two lens paragraphs). Don't edit the template
   itself — write the filled-in result to a new file.
2. Write that file to a scratch directory (`mktemp -d`), named
   `reading.html`, and copy `references/icons/` into that same directory
   (as `icons/`) so the `<img src="icons/...">` paths resolve:
   ```bash
   OUTDIR=$(mktemp -d)
   cp -R "<skill-dir>/references/icons" "$OUTDIR/icons"
   # ...write $OUTDIR/reading.html here...
   ```
3. Serve it on localhost and open it:
   ```bash
   PORT=8420
   while lsof -i ":$PORT" >/dev/null 2>&1; do PORT=$((PORT+1)); done
   (cd "$OUTDIR" && python3 -m http.server "$PORT" >/dev/null 2>&1 &)
   sleep 0.4
   open "http://localhost:$PORT/reading.html" 2>/dev/null || xdg-open "http://localhost:$PORT/reading.html" 2>/dev/null
   ```
4. Always give the clickable `http://localhost:PORT/reading.html` link in
   chat too, even if auto-open worked — some environments won't have a
   browser to pop.

The page fetches Roboto / Roboto Mono / Roboto Condensed from Google Fonts
to match the DevSeed brand (per the devseed-poster skill's brand values),
with system-font fallbacks already in the CSS — if the machine is offline,
it degrades gracefully rather than breaking. Entrance and ambient animation are
tasteful and slow by design, and fully disabled under
`prefers-reduced-motion: reduce`.

This is a background local server for one static file. No cleanup logic
needed — it's cheap to leave running, and the user can close the terminal
or kill the process whenever. `ponytail: single background http.server per
reading, no lifecycle management — add teardown if the user runs enough of
these to care.`

## Step 6 — recap in chat

After the page is up, give a short recap (one line per card — name and
which position) so the substance exists even before anyone clicks the link.

## Privacy notes

- Never name specific people, even generically identifiable ones ("your
  quietest contributor") — describe work and themes, not people.
- Never quote file contents, credentials, or anything that looks like a
  secret. Subjects and filenames only.
- Don't fabricate context that isn't there — if a repo is quiet or has no
  git history, say so plainly rather than inventing drama for the sake of a
  good reading.

## Where things live (markdown vs code)

The split is deliberate — change things in the right layer:

- **Markdown (`SKILL.md`, `deck.md`)** holds everything that needs judgment
  per reading: the flow, tone and privacy rules, card meanings. Claude reads
  these fresh each run, so interpretation adapts to the repo at hand.
- **Code (`template.html`, `icons/*.svg`)** holds everything that should be
  identical every run for every user: layout, the welcome/turn ritual,
  animations, brand tokens. No judgment, no drift.
- The seam is the `{{TOKEN}}` contract in the template. Only reading-specific
  words cross it. Nothing repo- or person-specific may be hardcoded on the
  code side — that's what keeps the skill portable to any project.

## Sharing this skill

Built to be portable — no dependency on this vault's structure, no hardcoded
paths. To share with other DevSeed folks, this whole folder can go into
`developmentseed/ds-skills` (same path other TPL skills like
`ds-role-explorer` took) — copy `.claude/skills/devseed-tarot/` as-is.
