---
name: bd-roadmap
description: Build a Development Seed BD roadmap (12-18 months out) as a markdown research doc plus a self-contained, DevSeed-branded HTML walkthrough with per-section feedback capture. Use when someone asks for a BD roadmap, a strategy refresh, a pipeline pattern read, or "where should BD focus next" — optionally scoped to focus areas like the EU, agentic AI, a vertical, or a specific account.
---

# BD Roadmap Builder

Produces two artifacts, plus one optional private note:

1. **`roadmap-<horizon>.md`** — the research doc: evidence, patterns, horizons, scenarios, open questions
2. **`walkthrough.html`** — the same content as a self-contained, DevSeed-branded page the BD team can walk through and annotate. No hosting needed, send the file directly
3. Optional **source note** (kept out of anything shared) holding exact figures if the runner provided them

Nothing in the output is a decision. The closing stance of every roadmap: *the point is to argue with it.*

## Step 0 — scope it

Ask for (or pull from the request):

- **Horizon**: default is the rest of this calendar year plus the next one
- **Focus areas to weight**: e.g. EU institutional, agentic AI, a vertical (disasters, climate risk, agriculture), a partner segment (philanthropy, development banks), an account. Focus areas change research depth and which scenarios get built — they don't change the structure
- **Audience**: BD team by default
- **What internal sources exist**: strategy docs (islands / State of Tech), labs or R&D notes, staffing signals, anything in the current workspace

## Step 1 — gather the evidence

**Pipeline facts.** Ask the runner to paste or drop an export (CSV or a written summary) covering the trailing ~12 months: wins, losses, deliberate no-gos, and open deals with stages. Work only from what they provide — do not go fetch pipeline data from any live system. Amounts are optional; the roadmap works with size bands (Step 3).

**Strategy context.** Read whatever internal docs the workspace has: islands/State of Tech, labs priorities, recent staffing tickets (open roles are a demand forecast).

**Outside research.** Web research, current-dated, on:
- Funding climate for the anchor clients (NASA budget cycle, ESA/EU programs like Copernicus, Destination Earth, the EU multiannual budget)
- **The upcoming funding calendar**: concrete calls, tenders, and recompetes over the next 6-24 months with dates and sizes — ROSES elements, NSF, NOAA vehicles, ESA ITTs (esa-star), Destination Earth procurement, Horizon Europe work programmes, EOSC calls, national agencies (UKSA, CNES, DLR), development banks, and philanthropy rounds (Bezos, Google.org). Note eligibility mechanics (US entity vs EU consortium roles, small-business set-asides, for-profit-can't-lead cases) — eligibility often matters more than fit
- Buyer segments expanding geospatial/EO spend (climate risk & insurance, energy, development banks/UN, philanthropy)
- Foundation models and agentic AI in geospatial — what hyperscalers give away free, where the paid services gap is
- **What peer consultancies and product entrants are doing**, ending in a ranked competitive white-space list: positions nobody credible occupies yet that this team could take

Cite every claim with a URL and flag strong (multi-source) vs speculative. Parallel research subagents are worth it here (one per lane: competitors, funding per core region, other regions). Keep the full sourced detail in a companion research note next to the roadmap, and pull only the sharpest items into the roadmap itself.

**The live bid shortlist.** After the program-level research, run a second sweep for solicitations that are actually open or imminent, and score them. This is the part BD teams act on the same week:

1. *Sweep the real sources, not program pages*: SAM.gov/grants.gov/NSPIRES (note which recurring omnibus elements are between cycles and when they reopen), NSF solicitation pages, esa-star public tender actions, the EU Funding & Tenders portal, DestinE/ECMWF/EUMETSAT procurement pages, TED, UNGM and MDB portals, national agencies, foundation open calls. Record which portals are login-walled and say so rather than guessing.
2. *Cross-check the pipeline*: never recommend something already being bid — instead flag if the live call is bigger than the pipeline entry suggests (an under-sized pursuit is a finding).
3. *Score each item against three filters*: **strategy** (focus areas, open source posture, declared no-go markets), **value pattern** (does it match the win archetype from the pattern read, does it avoid the loss archetype), **size and eligibility** (can the team staff it, prime vs sub vs associated partner, for-profit leadable, set-asides, entity/registration requirements — eligibility kills more bids than fit does).
4. *Output pursue / watch / pass*: pursue items get a close date and a named next move, watch items get the condition that would activate them, pass items get the reason on record so the decision isn't relitigated.
5. *Name the standing infrastructure* the shortlist implies: release-day sweeps for recurring omnibuses, one-time portal registrations, and the partner bench for prime-blocked calls (university partners for grants a for-profit can't lead, consortium primes for agency tenders).

**Other regions, honestly.** Alongside the core regions, run one lane on everywhere else the team could plausibly work. For each region: the concrete funded programs, who actually pays and how reliably, and the downsides stated plainly (procurement opacity, local-presence/in-country-value regimes, payment risk, values/surveillance-adjacency, travel cost vs deal size, intermediation). End it ranked: worth deliberate effort / opportunistic only / skip, with the deciding factor named. Downsides are the point of this section — a regions list without them is marketing.

## Step 2 — the markdown roadmap

Eight sections, each answering one question:

1. **Where we stand** — the 4-6 facts that define the starting position (anchor contracts, record quarters, open pipeline total, team size, strategy state)
2. **What the pipeline is telling us** — the 3-4 strongest signals in the win/loss record, each stated as a claim with named evidence
3. **The pattern read** — the section BD teams use most:
   - *Most likely successful project* — the archetype, with the ladder examples (small study → platform, extension → flagship)
   - *Most likely unsuccessful project* — the archetype every recent loss fits
   - *Wins that then wobble, and why* — subcontract positions, weak-premise engagements, pilots that reshape mid-flight, single-point-of-failure staffing, one-offs that don't compound
   - *Most underestimated* — the small deals carrying option value
   - *Numbers a BD eye should hold* — average deal age, no-go discipline, stage concentration
4. **Outside weather** — the researched trends, each with a "so what" for us, plus four evidence blocks: a **funding calendar** (dated table, soonest actionable first, with the "our move" column), a **competitive white-space read** (who the named watch item is, what's being commoditized, which positions are unclaimed), an **other-regions read** (worth effort / opportunistic / skip, downsides stated plainly), and the **live bid shortlist** (pursue/watch/pass table, the part that gets acted on this week)
5. **The roadmap** — three horizons (H2 now-year, H1 next-year, H2 next-year), 4-6 items each, verbs first
6. **Islands / strategy areas** — what changes in the strategic bets, including any new area the evidence argues for
7. **Scenarios** — two upside, two downside. Each: signal to watch, pre-move now, what we'd do if it hits. Note which pair is the base case
8. **What we would have to believe** — five falsifiable statements, ending with the feedback ask

Voice: plain, first person plural, measured claims, no hype. Every recommendation is arguable and says so.

## Step 3 — the sensitivity rule (non-negotiable)

Anything that could be shared beyond the immediate team uses **size bands, never exact per-deal figures**: `S` under $100K · `M` $100-300K · `L` $300-750K · `XL` $750K+. Exact figures, if provided, go only in the separate source note. Aggregates (quarter totals, pipeline total) are fine only if they were already shared at company level or are public facts (a press-released contract ceiling). When in doubt, band it. State the banding scheme in the doc header so readers know it's deliberate.

**The outputs are confidential even when banded.** Write them to a private location (a private vault or repo), never to anywhere public, and keep the "don't circulate beyond the BD team" line in the walkthrough footer. This skill file is public; the roadmaps it produces are not.

## Step 4 — the walkthrough

Start from `references/walkthrough-template.html` — it carries the DevSeed brand (orange `#CF3F02`, Roboto Condensed / Roboto / Roboto Mono, warm off-white ground) with light and dark themes wired through CSS tokens, chart scaffolding, per-section feedback boxes (localStorage + a copy-all button formatted for a Slack thread), and a shared tooltip.

Fill each `SAMPLE` block with the real content. Rules that keep it honest:

- Charts are single-hue (the brand orange), direct-labeled, with a `<details>` table fallback. No rainbow categoricals, no dual axes
- Every section ends with its feedback box and a real question, not "any thoughts?"
- Keep the band legend in the hero and the "don't circulate" line in the footer

Then make it self-contained — inline the Google Fonts so it works offline:

```bash
python3 - <<'EOF'
import urllib.request, base64, re
ua = {'User-Agent': 'Mozilla/5.0'}
url = 'https://fonts.googleapis.com/css2?family=Roboto+Condensed:ital,wght@0,400;0,600;0,700;1,400&family=Roboto+Mono:wght@400;500&family=Roboto:wght@300;400;500;700&display=swap'
css = urllib.request.urlopen(urllib.request.Request(url, headers=ua)).read().decode()
def inline(m):
    data = urllib.request.urlopen(urllib.request.Request(m.group(1), headers=ua)).read()
    return f"url(data:font/woff2;base64,{base64.b64encode(data).decode()})"
inlined = re.sub(r'url\((https://fonts\.gstatic\.com/[^)]+)\)', inline, css)
html = open('walkthrough.html').read()
html = re.sub(r'@import url\([^)]+\);', lambda m: inlined, html, count=1)
open('walkthrough.html', 'w').write(html)
print('self-contained')
EOF
```

QA before delivering: screenshot both themes with headless Chrome and actually look at them (label collisions, overflow, both grounds legible). Light theme: make a temp copy with `data-theme="light"` stamped on `<html>`.

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
  --screenshot=qa.png --window-size=1280,3200 --hide-scrollbars "file://$PWD/walkthrough.html"
```

## The lockstep rule

The markdown roadmap and the walkthrough are the same content in two forms. Any substantive change to one lands in the other in the same session — new sections, new evidence, corrected figures, removals. Never let the doc get ahead of the page. After every walkthrough edit, re-render (headless screenshot) and look at the changed region.

## Step 5 — deliver

Hand over both files. Remind the runner: the walkthrough needs no hosting, feedback notes save per-browser, and the copy-all button output is formatted to paste straight into a Slack thread.
