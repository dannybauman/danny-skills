# The Basemap Deck

Twenty-two cards, same role as a tarot Major Arcana: the big, recurring
shapes a project's life takes, reskinned around the stuff anyone who ships
software (or runs open geospatial data pipelines) already recognizes. No
people, no in-jokes that need a decoder ring — just concepts that land for
most repos, most teams.

Every card is drawn as a **chart fragment** — a small piece of an imagined
map, in a visual language borrowed from the world's many wayfinding
traditions: dotted journey paths, concentric place-marks, crossing swell
lines, navigation stars, knotted record-cords, storm spirals. Deliberately
abstract and syncretic — inspired by how humans everywhere have charted
their worlds (Pacific wave piloting, Andean khipu records, Mesoamerican
route glyphs, astrolabe geometry), never imitating any single tradition's
own iconography. Each card's `Chart:` line describes its scene.

Read top to bottom for a rough project-lifecycle arc (idea → build → strain
→ delivery → reflection → renewal), but any 4 can come up in any order.

---

**0 · THE GREENFIELD**
*A blank slate, no legacy to fight*
Chart: a lone departure point, a route fading into unsurveyed territory,
two islands still sketched in dashed outline — confirmed by nobody.
Nothing here has hardened into "the way we do it" yet. That's freedom, but
also no guardrails — the first few decisions get treated as gospel long
after everyone's forgotten they were arbitrary. Choose loosely, write down
why, and don't let an empty chart talk you out of a lightweight plan.

**I · THE OPEN SOURCE COMMIT**
*Work made for someone else's benefit*
Chart: a home port with routes radiating outward past the border of its own
map, toward islands it will never administer.
Something here was built to be useful past its original task — code, a doc,
a pattern — offered outward instead of kept local. It compounds slower than
a shipped feature but further: someone unrelated to this work will build on
it later without asking permission first.

**II · THE STAC CATALOG**
*The order was always there, just not indexed*
Chart: a knotted record-cord — many strands, many knots, one strand lit up
because someone finally knew where to look.
What you need already exists somewhere in here — it's a findability problem,
not a missing-information problem. The fix isn't more work, it's better
metadata: naming things so future-you can locate them without re-deriving
what you already knew.

**III · THE DATA PIPELINE**
*Quiet accumulation, nothing dramatic*
Chart: a steady ocean current carrying cargo, fanning out into a delta at
the far shore.
The valuable thing happening right now isn't visible in a demo. It's steady
and unglamorous — ingestion, cleanup, the boring infrastructure everything
else depends on. Don't mistake "nothing to show" for "nothing happening."

**IV · THE LEGACY SYSTEM**
*A structure you inherited, not chose*
Chart: an old waystation every route still converges on, crack running
through it, one bright patch holding it together.
Somewhere in here is a decision nobody currently on the project actually
made, but everyone is currently living inside of. Not automatically wrong —
it solved a real problem once. Worth asking whether that problem still
exists, not whether the structure is old.

**V · THE FORK**
*Divergence isn't betrayal*
Chart: one river braiding into two around an island, both channels reaching
their own destination.
A path is splitting — a new repo, a new approach, a new owner. Looks like
fragmentation from outside. Usually it's specialization: two things that
used to share one shape needed different ones, and forcing them to stay
merged would have served neither.

**VI · THE POD**
*Small, trusted, and enough*
Chart: three settlements in a tight triangle around one shared hearth.
The unit doing the real work here is smaller than the org chart suggests.
Not a staffing gap — usually the actual advantage. A tight group that
doesn't need a meeting to know who owns what moves faster than a large one
that does.

**VII · THE SPRINT**
*Focus under a deadline you didn't soften*
Chart: a single day's crossing — sunrise to sunset arced overhead, a taut
route between two shores, no anchorages marked.
Something is being tested in a short, high-stakes window right now — code,
a candidate, a proposal. The compressed timeline is doing real work: it
surfaces what actually matters under pressure, which a longer runway would
have let you avoid deciding.

**VIII · THE COG**
*Efficient by design, not by accident*
Chart: an astrolabe — nested measuring rings, one needle reading exactly
the mark it needs and nothing else.
Something here does more with a smaller footprint on purpose — structured
so only what's needed gets touched or moved. Unglamorous craftsmanship:
nobody notices good architecture, they just notice when it's absent.

**IX · THE ASYNC HANDOFF**
*Trust extended across silence*
Chart: two islands with no route between them, both taking a bearing on
the same star.
Work is passing to someone in another time zone, role, or day, and you won't
see it land. Not a loss of control — the actual mechanism of distributed
work: writing clearly enough that your explanation doesn't need you present
to be understood.

**X · THE SCOPE CREEP**
*The ask that kept growing*
Chart: one small surveyed territory, ringed by successively larger dashed
resurveys nobody remembers commissioning.
Something reasonable-sounding got added, then another reasonable-sounding
thing, and now the original shape is gone. Nobody said yes to the whole pile
at once — that's exactly how it happens. The fix isn't refusing asks, it's
naming the boundary out loud before the next one arrives.

**XI · THE MERGE CONFLICT**
*Two truths, both partly right*
Chart: two swell systems crossing — the pilot's marks sit exactly where the
wave sets interfere.
Two versions of the same thing changed in incompatible ways, and someone has
to actually read both before resolving it, not just pick a side. The urge
to auto-resolve and move on is exactly the urge to fight — the conflict is
flagging something that genuinely needs a judgment call.

**XII · THE OPEN PR**
*Suspended between done and accepted*
Chart: a vessel holding position outside the harbor, reef bar across the
entrance, waiting on the tide.
Something is finished from where you're sitting but not yet real — waiting
on someone else's attention, review, or sign-off. Uncomfortable but not
wasted time: the waiting is often what makes the eventual merge trustworthy.

**XIII · THE POSTMORTEM**
*Naming it plainly is the release*
Chart: a wreck site, carefully sounded and surveyed, with the new safe
route drawn wide around it.
Something broke, or ended, or didn't go the way anyone planned, and it needs
to be looked at directly rather than smoothed over — not to assign blame,
to update the model of what's true. The reef only sinks the next crew if it
never makes it onto the chart.

**XIV · THE REBASE**
*Same history, better order*
Chart: the old meandering track still faintly visible, the clean replotted
course laid over it — same departure, same landfall.
The story of how you got here is getting rewritten — not to change what
happened, but to make it legible, pulling the useful thread out of a tangle
of false starts. What looked like chaos in the moment can read as a clean
line in retrospect, if someone takes the time to tell it that way.

**XV · THE WILDCARD TICKET**
*Nobody scoped this, and here it is*
Chart: a plotted route interrupted mid-passage by an eddy no survey
mentioned, detour bending around it.
Something unplanned just landed — not necessarily a crisis, just genuinely
unaccounted for. Not a sign anyone planned badly; some fraction of the work
is always the thing nobody could have listed in advance. Budget for it
existing, not for eliminating it.

**XVI · THE OUTAGE**
*What looked stable, wasn't*
Chart: a storm spiral over the shipping lane, the route scattered to
fragments, one beacon dark.
Something everyone assumed would hold gave out fast, and now it's visible
to people who weren't watching before. The sharpest card in the deck, and
the most honest — it ends a kind of denial faster than any retro would
have. What rebuilds after tends to be sturdier than what it replaced.

**XVII · THE DASHBOARD**
*Signal separating from noise*
Chart: a star compass — the full ring of the night sky, three stars lit,
bearings drawn to the center.
Clarity is arriving — not because more happened, but because something
finally got measured and shown plainly. Once a number is visible, decisions
that were arguments of opinion become much easier to have. The hard part
was never the chart, it was agreeing what to measure.

**XVIII · THE RETRO**
*Looking back without assigning blame*
Chart: the completed voyage laid out astern, knots marked along the track,
one moment held under the reading glass.
Something just wrapped, and the useful move now is honest reflection, not
a victory lap and not a flogging. What gets named here quietly, in a room
that feels safe, is the thing that doesn't repeat next time. Skipping this
step is the most common way lessons get re-learned the expensive way.

**XIX · THE BIG TENT**
*Everyone under one roof, briefly*
Chart: routes from every edge of the map converging on a single gathering
ground.
Separate threads of work are about to become visible to each other — one
room, one channel, one meeting, if only for a moment. Things that made
sense in isolation get tested against people who weren't in the original
conversation. Disorienting and clarifying in the same breath.

**XX · THE TEAM WEEK**
*Distance collapses, on purpose*
Chart: one shoreline holding every hearth at once, moon phases overhead
marking how briefly the season lasts.
A rare, deliberate stretch of full presence is coming, or just happened,
cutting through months of async-by-default. What gets decided or repaired
in that window sticks longer than it should, precisely because it was
earned by everyone actually being in the same place at once.

**XXI · THE RELEASE**
*A hundred small decisions, now just "done"*
Chart: an island drawn solid at last — its dashed ghost still faint beside
it — with other people's routes already bending toward it.
Something shipped — tagged, live, out the door, already becoming
background rather than the main event. Sit with this one before turning to
the next greenfield: it's on the map now, and other people will navigate
by it without ever knowing it was once a dashed line.
