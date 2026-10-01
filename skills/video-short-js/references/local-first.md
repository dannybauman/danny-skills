# Local-first mode

A way to build the film with most tokens spent by a local model and few by the cloud. It comes from three
builds of the same 60-second film on a 16 GB Apple Silicon laptop that its owner was using at the same time:

| Build | How | Local share of all tokens | Result |
|---|---|---|---|
| 1 | Cloud wrote everything | 0.01% | A good film |
| 2 | A local model wrote the content as small tested completions; one long-lived cloud agent wrote the harness | 2.8% (62% of the words written) | It ran; the drawings were unrecognisable and a cold viewer read the story as "isolation", the opposite of the brief |
| 3 | Build 2's harness run as scripts, a 6K-token standing brief on every local call | 3.9% when stopped at 136 local calls | Stopped: the cloud session supervising it was the cost |

The tools in `starter/tools` (`run.sh`, `local.py`, `cloud.py`, `ledger.py`) are what builds 2 and 3 proved,
made general. `scripts/selftest-local.sh` checks the driver with a stub model.

## Read this first: what is not proven

- **"The local model directs with a parts kit" has not been run end to end.** It is the design that came
  out of build 3, not a measured result. Builds 2 and 3 had the local model draw.
- **No build has reached a majority of tokens local when everything is counted.** The best was 3.9%. The
  arithmetic says it is possible (at 1.5M local tokens an hour, five hours of local work against a 3-5M
  cloud build is about 55%), but nobody has done it.
- The drawings a small model makes are worse than the cloud's. Expect a worse film unless the pictures come
  from a kit.

## When to use it

- The owner asks for local models to do as much of the work as possible, or cloud tokens are scarce.
- There are hours of laptop time to spend, and a local text model already on disk (no downloads).
- The film can be described as data: placements, timings, notes, words. If it needs new drawings that
  nothing in the kit can make, those drawings stay a cloud job or the film gets worse.

Do not use it when the film must be as good as possible soon: the local builds took hours of laptop time
(build 2: 2.45 h of model time inside about 3.5 h) and looked worse.

## Where cloud tokens actually go

Every message a cloud session sends re-sends its whole context. That, not the writing, is the cost.

- A fresh session's first message was about 45K tokens and grew to 65-220K as it read files.
- The session supervising build 3 had about 800K tokens of context, so each reply cost about 0.85M. Twenty
  replies cost 16M, 80% of that build's cloud total. A session also replies when a background
  helper or tracked task posts a "finished" or "still running" notice, and each such wake costs one of these.
- A one-shot `claude -p` call was 78K tokens by default and 33.6K stripped (the shape in `tools/cloud.py`).
  `--bare` needs an API key and fails with "Not logged in" on a subscription login.

Reported elsewhere, and consistent with this: Claude Code's cost guide says context size drives cost and
recommends clearing between tasks (https://code.claude.com/docs/en/costs); headless `claude -p` runs one
request and exits (https://code.claude.com/docs/en/headless); Anthropic's agent guidance prefers fixed
workflows to open-ended agents when the steps are known
(https://www.anthropic.com/engineering/building-effective-agents); and the Minions paper has a cloud model
write job specs that local workers run (https://arxiv.org/html/2502.15964v1). Minions was tested on reading
tasks, not on generating a film.

## The split

**A script orchestrates; no cloud session stays open during the run.** The pipeline is fixed, so a shell
script runs it: `tools/run.sh` and the units in `local/pipeline.sh`. State lives in files. Launch it
detached and end the session. Do not supervise it from a session, do not run it as a tracked background
task, and do not spawn helpers to watch it: each of those wakes the session, and every wake re-reads the
whole context.

**The local model writes data and makes choices; it does not draw from raw coordinates.** Gemma 4 E4B
passed staging, timing, plans, notes and review tasks. Its polygon drawings failed a blind vision check 10
times in 19. So give it a parts kit: a drawing library (written once, by the cloud or by hand) and a short
catalogue of its parts (name, parameters, size, anchor points, what it looks like in one line). The local
model then writes the cast and layout, each shot as keyframed placements of parts with poses and camera,
the cue sheet, narration, the score's notes, the sound events, and review notes. A thin stage turns the
data into frames. Say plainly in the credits which drawings came from the kit.

**Cloud is a handful of logged one-shot calls** through `python3 tools/cloud.py <task> < prompt`, from an
empty folder, each logged to `local/cloud_usage.jsonl`:

1. Up front: one call for the parts catalogue, or the recipe the local units follow, if you do not write it
   while building.
2. Takeovers, only for a piece the local model failed three times. Send that piece's spec, the failing
   output and the test message, nothing else. Build 2 took over 2 of 9 shots after 12 failed attempts each.
3. One final review, of a contact sheet description or a few frames.

Cap it at about 15 calls: at 33.6K tokens each before the prompt itself, that is about 0.5M.

## Local calls that work

All measured in builds 2 and 3 with llama.cpp `llama-server`, thinking off, `--parallel 1`, q8 KV cache.

- **A standing brief at the start of every text call, byte-identical.** The brief, the cue sheet, the parts
  catalogue, what went wrong before, two passing examples. Because it is identical, the prompt cache serves
  it: in build 2, 73% of all prompt tokens came from the cache; in build 3 a brief of about 6K tokens gave
  about 1.5M local tokens an hour. Put it in a file and pass `--brief`; put the task last. Changing one
  byte of it costs a full re-read on the next call.
- **Two to four candidates, chosen by tests.** In build 2, 125 sprite calls gave 49 passing outputs; with
  two candidates and three attempts each, 20 of 21 sprites passed in the first batch.
- **Fixed seeds per (task, attempt), and change the prompt when you retry.** A repeated prompt with the
  same seed returns the same answer; one layout failed identically three times.
- **Error messages that say where the failure is.** "Cannot read properties of undefined" fixed nothing in
  three tries. "At line 3 of your code: piece(c, xf([1,2],0,0), {})" was usually fixed next try. The same
  for timing: "at t=1.5 it is at screen x -200, y 50 with alpha 0.8".
- **Validators that check meaning, not wording.** Demand the story beats (three crashes between 4 and 18 s,
  calm while building, a shot boundary at every act); normalise trivial format ("Dorian" and "dorian").
  Over-strict format checks cost about 15 calls in build 2.
- **Judge pictures blind.** Ask "what is this a picture of?", never "this is meant to be X: yes or no?"
  Told the answer, the vision model said yes to 18 of 19 sprites. Blind, it named 6 of 19, and 9 after one
  repair each. Feed what the blind viewer saw into the next repair. For choices, ask pairwise, twice, with the order swapped, and keep
  a pick only if it survives the swap. Add a short checklist per shot: are the characters visible, is this
  beat's action happening, is anything off frame.
- **One model loaded at a time.** Loading Gemma E4B took free memory from about 60% to 19-27%; a 9B vision
  model with its projector from about 72% to 13-19%. Text and vision batches never shared memory.

Choose the model by a short benchmark of the real tasks (three tasks, three attempts each), by pass rate
then speed. In build 2 Gemma 4 E4B passed at 34 tokens a second; Qwen 9B was slower (19) and failed a task.

## Running it

```bash
export LOCAL_TEXT_MODEL=/path/to/text-model.gguf            # already on disk; nothing is downloaded
export LOCAL_VISION_MODEL=/path/to/vision.gguf LOCAL_VISION_MMPROJ=/path/to/mmproj.gguf   # or let local_viewer's search find one
cp local/pipeline.example.sh local/pipeline.sh               # then write the film's units
tools/run.sh                    # start, or resume; detached; log in local/run.log
tools/run.sh status             # local/STATUS.txt (rewritten after every unit) and whether it is alive; loads no model
tools/run.sh pause              # stops after the local call in flight and unloads the model
nohup tools/run.sh pause-at 18:30 >/dev/null 2>&1 &           # the owner wants the laptop back at 18:30
nohup tools/run.sh resume-when-free >/dev/null 2>&1 &         # resume once memory free is 42% or more
python3 tools/ledger.py --session <session.jsonl> --build <session.jsonl>
```

A unit is one `step <id> <text|vision|path|-> <command>` line: one shot, one sprite, one review, small
enough to redo from its start. Its command asks the model with `python3 tools/local.py ask <task>
[--brief F] [--image F] < prompt` and writes its result to `$UNIT_OUT`. What the driver guarantees:

- Each unit's result, then its done-marker, is written atomically (temp file, then rename). A rerun skips
  finished units; a unit cut short is redone from its start.
- `pause` (or `touch local/PAUSE`, SIGINT or SIGTERM to the run) lets the call in flight finish, then the
  next `ask` exits 75, the run stops and the model is unloaded.
- Start stops a model server left by a killed run (its pid file names it), then resumes.
- Before every model load: at least 40% memory free and 3 GB disk, or the run pauses and says why. During
  calls, under 8% free makes the next call wait.
- Running time counts only time spent in units. Build 3 capped its rounds on wall time since the first start,
  so every pause ate into the budget; `python3 tools/local.py elapsed` is the corrected clock for caps.

Observed in build 3: a pause set for a clock time stopped cleanly with the model unloaded and free memory
back to 63%; resume skipped finished units; the waiter resumed the run once memory rose above the load
guard. The selftest repeats pause, SIGTERM, a hard kill and resume with a stub model.

## The accounting

Decide nothing silently; show both views (`tools/ledger.py`):

- LOCAL = prompt + completion tokens of every local call (cached prompt tokens count, as cloud cache reads do).
- CLOUD, the run = the one-shot calls plus any session messages sent while the run was going.
- CLOUD, everything = the run plus the session that built the pipeline.

The "everything" view is the honest one. Build 3 was 3.9% with everything because the session that built
and supervised it dwarfed the local work. Session records are de-duplicated by
message id: a streamed message is logged several times.
