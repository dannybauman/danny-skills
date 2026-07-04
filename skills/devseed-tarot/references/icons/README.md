# The Basemap Deck — card art

Every card is a **chart fragment**: a small piece of an imagined map, drawn
in a shared wayfinding vocabulary so all 22 read as one deck.

## Design language

Inspired by the world's many wayfinding traditions — Pacific wave piloting
(crossing swell lines), Andean khipu record-keeping (knotted cords),
Mesoamerican route glyphs (dotted journey paths), astrolabe and star-compass
geometry. Deliberately kept at the level of **universal abstract marks**:
we borrow the shared human vocabulary of charting (paths, places, swells,
stars, knots, spirals), never reproducing any single tradition's own or
sacred iconography.

The recurring marks, so replacements stay in the same language:

| Mark | Meaning |
|---|---|
| faint dotted ring | the chart's graticule — on every card, the deck's unifying frame |
| concentric circles + dot | a place (port, settlement, waypoint) |
| dotted/dashed line | a route — dotted for footpaths/intent, dashed for sailed courses |
| long crossing curves | ocean swells; interference where they meet |
| four-point star / diamond | a navigation star |
| dot on a strand | a knot — a record, a data point |
| spiral | storm, eddy, hazard |
| organic closed blob | an island — dashed outline if unconfirmed, solid once real |

Two-tone: **gray `#9a9490`** for the geography (context), **accent
`#CF3F02`** for the story (the card's one idea). Works on light and dark
backgrounds.

## Swap contract

These are plain external SVGs referenced from `template.html` as
`<img src="icons/{filename}">` — deliberately not inlined, so this folder is
a drop-in slot for a different art set (an icon library, a designer's
custom art, photography, anything).

1. **22 files, same filenames**, matching `deck.md` / `SKILL.md` order:

   ```
   00-greenfield.svg          08-cog.svg                 16-outage.svg
   01-open-source-commit.svg  09-async-handoff.svg        17-dashboard.svg
   02-stac-catalog.svg        10-scope-creep.svg          18-retro.svg
   03-data-pipeline.svg       11-merge-conflict.svg       19-big-tent.svg
   04-legacy-system.svg       12-open-pr.svg              20-team-week.svg
   05-fork.svg                13-postmortem.svg           21-release.svg
   06-pod.svg                 14-rebase.svg
   07-sprint.svg               15-wildcard-ticket.svg
   ```

2. **Square, transparent background.** This set uses `viewBox="0 0 160 160"`;
   any square viewBox works (the fixed-aspect `.icon-frame` prevents
   distortion).

3. **Colors are baked in, not inherited.** Loaded via `<img>`, so page CSS
   can't recolor them. If a replacement set ships black or multi-color,
   either recolor to the two-tone palette above (usually a find-replace on
   fill/stroke values) or accept its palette as intentional.

4. **Raster formats work too** (`<img>` doesn't care) — keep them square
   and reasonably small.
