---
name: integrating-local-models
description: "Integrate a local LLM (Ollama / LM Studio) or local audio model (Whisper STT / Kokoro / Piper TTS) into an app or agent. Starts by sweeping for the decisions that need NO model (rung 0), then probes endpoint, completion, and tool-calling, picks the right provider, flags the completion-safe vs agentic-risky gate, and routes audio by privacy/offline/latency. Use when wiring a local model into an app or agent runner, deciding which steps should go local at all, choosing between Ollama and LM Studio, debugging local tool-calling or context-overflow failures, or picking a local STT/TTS model."
---

## What This Does

Helps you wire a local model into a real app or agent runner without the usual traps. The core is a capability probe that classifies a local endpoint into three **rungs**, because "the model runs locally" is not the same as "the model can do the job":

- **Rung 0 — no model at all.** The decision is a lookup, a rule, or a string comparison. Do this sweep *before* probing anything.
- **Rung 1 — reachable.** The server answers and lists models.
- **Rung 2 — completion.** A single-shot chat completion returns real text.
- **Rung 3 — tool-capable.** The model emits *structured* tool-calls the runner can execute, instead of describing them as prose.

### Rung 0 — sweep before you probe

**The cheapest, fastest, most reliable local decision is the one with no model in it.** Before choosing a model, enumerate every decision on the path you are trying to speed up and ask of each: *is this a lookup, a rule, or a comparison?* If yes it is rung 0, and a model is the wrong tool at any size — slower, less reliable, and unauditable next to a table read.

This reorders the whole integration. "Which model?" is the second question; the first is "which of these needs a model?"

**Why this rung exists (measured, 2026-07-18).** A voice-capture → triage pipeline was slow end to end and the obvious read was "it needs a local model to stop waiting on the cloud." The sweep found **23 of 28 decision points were rung 0**, and — the part that changed the plan — **16 of those were already implemented, and 7 were deterministic rules that ran inside a cloud LLM session purely because nobody had written them down as code.** The latency was prose-not-code, not absence-of-weights. Wiring the existing lookups closed most of the gap; the model tier shrank from "the whole decision layer" to the few genuinely judgment-shaped steps.

Expect this. A pipeline that grew organically accumulates rules in documentation and prompts, and an LLM session becomes the interpreter for them by default — it is the path of least resistance, not a decision anyone made.

**Signals a step is rung 0:**

- it resolves against a table, registry, allowlist, or config
- its answer is stable and auditable — same input, same output, forever
- you could write the assertion before the code
- a wrong answer is a *bug*, not a bad judgment call

**Signals it is not** — it needs summarizing, ranking, classifying open-ended input, or reading intent. Those are rung 2.

**Two traps, both seen live:**

1. **Don't force a judgment call into a heuristic to win the count.** A wrong rung-0 verdict is worse than a slow rung-2 one, because it is silent and confident. When a heuristic's false-positive would send work somewhere wrong, make it *decline* rather than guess, and let the model tier handle what it declined.
2. **Ship each rung-0 rule with a hermetic selftest, and name its money path** — the direction whose failure is expensive. Write the test for *that* case first. In the sweep above, two real defects were caught by selftests written this way and would otherwise have shipped silently.

**What rung 0 buys you beyond speed:** it runs anywhere. Rung 1+ needs the host with the weights — often a laptop, which sleeps and leaves the house. Rung-0 decisions run on the always-on box, so the latency-critical path stays alive while the model tier queues.

Rung 3 is the one that bites people: many local models, asked to use a tool, write `I'll call get_weather(...)` as **text** and never emit a real `tool_calls` object. An agentic runner then "describes" reading/writing files without doing it — silent wrong output. Completion work is safe at rung 2; agentic work needs rung 3 confirmed.

> Rung 3 confirms the model *emits* structured tool-calls — necessary, not fully sufficient: your harness must still execute them, and `probe.sh` only tests a *tiny* prompt. A model can pass `probe.sh` rung-3 yet still fail in a real agentic loop (see the context trap below). The sufficient check is `probe-opencode.sh` — it runs opencode for real and verifies a file + commit actually landed on disk.

## How to Run

```
bash ${CLAUDE_SKILL_DIR}/scripts/probe.sh                       # auto-detect LM Studio :1234 + Ollama :11434
bash ${CLAUDE_SKILL_DIR}/scripts/probe.sh --url http://localhost:1234/v1 --model qwen3.5-9b
```

`probe.sh` speaks the OpenAI-compatible wire format (`/v1`). LM Studio is OpenAI-compatible natively; Ollama exposes both its own API and an OpenAI-compatible `/v1`. It prints the highest rung reached per endpoint and the exact reason it stopped.

For **agentic** use, run the end-to-end check that proves opencode actually *executes* tools (writes a file + lands a git commit, verified on disk — not just emits):

```
bash ${CLAUDE_SKILL_DIR}/scripts/probe-opencode.sh --model lmstudio/qwen3.5-9b   # real file + commit = PASS
```

Before dispatching a step whose input is large (a transcript, a long doc), **preflight the memory budget** so a too-big source routes to cloud instead of swap-thrashing the machine:

```
bash ${CLAUDE_SKILL_DIR}/scripts/ctx-budget.sh --source-chars 72000   # LOCAL-SAFE / WITH-LEVERS / ROUTE-TO-CLOUD
```

## Choosing the Provider (the integration decision)

Two local providers, **two different integration shapes** — don't assume "local == Ollama":

| Tool | API shape | Default port | SDK provider |
|---|---|---|---|
| **Ollama** | its own native API | `:11434` | `ollama-ai-provider-v2` (or its `/v1` via openai-compatible) |
| **LM Studio** | OpenAI-compatible | `:1234/v1` | `@ai-sdk/openai-compatible` |

Start LM Studio headless: `lms server start`; list models: `lms ls`. Don't tell the user to download new models — probe what they already have.

## The @ai-sdk Version-Match Trap

When using the Vercel AI SDK (`ai` + `@ai-sdk/*`), **every provider must share the same `@ai-sdk/provider` major** or they won't interoperate. The package major is NOT a reliable signal — check the dep:

```
pnpm view @ai-sdk/openai-compatible@<version> dependencies   # match @ai-sdk/provider to your other providers
```

Example: with `ai@^6` + `@ai-sdk/anthropic@3` (→ `@ai-sdk/provider@3.x`), the right `@ai-sdk/openai-compatible` is the **2.x** line (also `provider@3.x`), NOT `@^3` (whose only 3.x is a beta pulling `provider@4`, which breaks interop). Pin the exact version; don't blind-`^latest`. Use the project's package manager (detect `pnpm-lock.yaml` / `package-lock.yaml` first — `npm install` in a pnpm repo throws a cryptic null error).

Or just run the checker (reads your installed provider major from npm-flat *or* pnpm layouts and compares):

```
bash ${CLAUDE_SKILL_DIR}/scripts/check-aisdk-compat.sh @ai-sdk/openai-compatible@2.0.50
```

Exit 0 = safe, 1 = mismatch (with the dist-tag hint to find the right line).

## Gate the Agentic Path

- **Completion tier** (single-shot text) — safe on any rung-2 local model. Wire it freely.
- **Agentic tier** (multi-turn, tool-calling, file writes) — selectable ONLY after rung 3 passes for the chosen model. Default it OFF and require explicit operator confirmation; never let a client request silently pick an unconfirmed local agentic backend. Validate the backend id server-side at the dispatch seam, not just in the UI.
- **Always ship a cloud fallback.** A local agentic backend *will* fail on heavy steps (the capacity ceiling — see `references/gotchas.md`) — so a big-context cloud agent (e.g. claude-code) must be a first-class fallback, not an afterthought. Surface it **at the failure point**: detect the capacity/context error in the run UI and offer a "switch to claude-code" action right there (then let the user resume the failed step), instead of a dead-end error that buries the recovery path in settings.

For the agentic tier, a runner like **opencode** can drive a local model: add the provider to `~/.config/opencode/opencode.json` as an `@ai-sdk/openai-compatible` entry (`lmstudio` → `:1234/v1`, `ollama` → `:11434/v1`) with `tools: true` per model. This only works with a model that survives a *real* opencode loop — confirm with `probe-opencode.sh`, then still keep your own server-side tool-capable gate in front of it. Note `tools: true` is operator-*declared*, not measured (qwen2.5-coder carries it and still fails) — so if you auto-build a model menu *from* `opencode.json` (good: reflects the operator's real models, not a static list), don't treat every `tools:true` entry as agentic-ready; gate on `probe-opencode.sh` or carry a per-model caveat.

## Routing Strategies & Model Picks

When local handles the light steps but wedges on a heavy one, route **per step** (heavy/unbounded → big-context cloud; bounded file-in/file-out → local) or decompose the heavy step into bounded sub-invocations — don't force the whole run to cloud. For verified model picks (qwen3.5-9b passes; qwen2.5-coder:7b fails despite `tools: true`; Gemma 4 12B is a real contender) and the Ollama-vs-LM-Studio tool-call-fidelity note, read `references/routing-strategies.md`.

## Local Audio Models (STT / TTS)

Audio models are transform steps (audio→text, text→audio) — the rung-3 tool-calling risk doesn't apply to them; it lands on the *agent consuming* the transcript. Route audio local for privacy + offline + latency; keep orchestration on a rung-3 model. For Whisper model/runtime picks, Kokoro/Piper TTS trade-offs, the reuse-the-same-`/v1`-client trick, resource discipline, and urgency-based routing, read `references/local-audio.md`.

## Gotchas That Cost Hours

Read `references/gotchas.md` before debugging a hang, an overflow, or "this model won't tool-call." Headlines: **64K context is the FLOOR** for real agentic steps (LM Studio errors loudly on overflow; Ollama silently truncates to 4K and tool-calling "breaks"); LM Studio's JIT can spin up a **second default-context instance under the bare model id** (`lms ps` showing two rows = the bug — fix with `lms unload --all` then `lms load … --identifier <bare-id>`); the runner **never starts the model host** and a dead endpoint hangs silently — preflight `curl -fsS http://localhost:1234/v1/models` before every dispatch; probe serially; don't edit app source mid-run.

## Verify Before Claiming It Works

Provider construction is lazy — a backend object resolves fine with the server down. Prove it end-to-end: probe the endpoint, then run one real generation. Reasoning models (qwen3.x, deepseek-r1) emit thinking tokens, so for **completion / probes give generous `max_tokens`** or the visible content comes back empty (a 10-token cap returns `""` — the budget went to `<think>`).

**But for agentic / tool-calling steps, do the opposite — turn thinking OFF.** The reasoning budget you want for a probe is dead weight in a tool loop: it burns 300–5000 tokens per call against your scarce 16GB context budget and can muddy tool-call emission. Pass `"chat_template_kwargs": {"enable_thinking": false}` in the request (it's a trained weight behavior in Qwen3.x, not a prompt trick), and regex-strip `<think>…</think>` as a belt-and-suspenders fallback. This is one of the cheapest levers for fitting a real step under the context ceiling.
