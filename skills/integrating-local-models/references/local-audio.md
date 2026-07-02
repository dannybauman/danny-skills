# Local Audio Models (STT / TTS)

Audio models are a different shape from LLMs: they're **transform steps** (audio→text, text→audio), so the **rung-3 tool-calling risk does not apply to them** — there's nothing to "describe instead of execute." The completion-safe vs agentic-risky gate still matters, but it lands on the *agent consuming* the audio, not the audio model: a local Whisper transcript fed into an agentic loop is only as safe as that loop's model (still needs rung 3 for vault writes/commits). **Route audio local for privacy + offline + latency; keep the orchestration on a rung-3 model.**

## STT — Whisper is the default, and smaller models punch above their size

The practical sweet spot is a **semi-small Whisper** model — you rarely need `large` for dictation:

- **`base` / `small`** (and the English-only `.en` variants) are the everyday picks — fast, low memory, accurate enough for clear dictation. `small.en` is a strong default for English voice-capture workflows.
- **`medium`** when accents/noise hurt accuracy and you can spare the RAM/latency.
- **`distil-whisper`** (`distil-small.en` / `distil-medium.en`) — ~roughly half the size/latency of the matching Whisper at close accuracy; reach for it when latency matters.

Runtimes, pick by platform:

| Runtime | Best for | Notes |
|---|---|---|
| **whisper.cpp** | Mac/CPU, embedded | GGML/GGUF weights, Metal + CoreML accel on Apple silicon; single binary, no Python. |
| **faster-whisper** (CTranslate2) | Linux/GPU servers | int8/fp16, markedly faster than reference `openai-whisper`; the server build is **Speaches** (OpenAI-compatible `/v1/audio/transcriptions`). |
| **WhisperKit** (Argmax) | on-device iOS/macOS | Swift + CoreML, optimized for Apple silicon — this is the phone-capture / offline-baseline path. |

## TTS — local trades inline control for privacy/offline

- **Kokoro (82M)** — the local quality leader for its size; ONNX, 24 kHz, several voices, faster-than-realtime on modest hardware. Default local TTS.
- **Piper** — fast/light, runs on a Raspberry Pi, but robotic and **no expressive control** — fine for status read-back, not for pleasant long-form.
- **Gotcha — no inline pacing tags locally.** Unlike cloud engines (e.g. Gemini 3.1 Flash TTS with `[slow]`/`[fast]`/pause tags), Kokoro/Piper have **no reliable inline style/pace control**. Implement pacing *behaviorally*: have the LLM shorten/re-render, and chunk by sentence with a per-chunk speed/rate param — don't expect SSML to land. So pacing-critical work either accepts behavioral pacing or stays on a cloud engine; don't promise tag-level control on local TTS.

## Reuse the same `/v1` client shape

You don't need a bespoke audio client: OpenAI-compatible local servers exist for both directions — **Speaches** (faster-whisper) exposes `/v1/audio/transcriptions`, and **openedai-speech / Kokoro-FastAPI** expose `/v1/audio/speech`. Point the same OpenAI-compatible client at `localhost`. This keeps the integration seam identical to the LLM path and lets you swap cloud↔local per step.

## Verify before claiming it works (audio edition)

Same ethos as the LLM probe — prove it end to end, don't trust that the process booted:

- **STT:** transcribe a known 5–10s clip and check the text, *and* check **real-time factor** (does a 10s clip transcribe in <10s on the target device? if not it can't keep up with live dictation).
- **TTS:** synthesize a sentence and actually listen — check sample rate (Kokoro is 24 kHz; a mismatch plays chipmunked/slowed) and time-to-first-audio for the streaming case.

## Resource discipline (don't overload the device)

Audio models are not free even when they're small, and they compete with the LLM for the **same RAM/GPU** — see the 16GB memory-discipline gotcha in `gotchas.md`; audio stacks on top of that budget. The trap is the "do it all on one Mac" instinct: live STT **+** a resident draft LLM **+** TTS read-back running concurrently on an M1 will thrash swap and stutter all three at once.

- **Don't co-resident a heavy LLM and audio models.** A 9B at 64K KV already pins ~7–8GB; add Whisper-`medium` + Kokoro and you're over the line on 16GB. Prefer **small Whisper** (`small.en`/`distil-small.en`) and unload what you're not using (`lms unload --all`, `ollama stop`).
- **Split work across devices instead of stacking it.** Push capture STT to the **phone** (WhisperKit, on-device) while the **desktop** runs the orchestration LLM — a natural capture-on-the-go topology — rather than loading both on one machine.
- **Serialize, don't parallelize.** Capture → think → speak as distinct phases; one heavy model resident at a time beats three fighting for wired memory.
- **Measure resident set, not just "it ran."** A model that loads fine solo can lock the machine the moment a second one joins; check memory pressure with everything you intend to run *simultaneously*, not one at a time.

## Route by urgency (queue local, escalate when rushed)

The cleanest way to keep local audio from overloading a device is to route on **time-sensitivity**, not just privacy:

- **Background / not-rushed → queue for local Whisper.** Bulk transcription, "process these voice memos later," anything without a human waiting — drop it on a local queue and let one small Whisper chew through it serially. Cheap, private, zero cloud cost, and it never competes with a foreground model because the queue runs when the device is idle.
- **Interactive / rushed, or weak device → escalate.** When a human is waiting on the words, or the capture device can't run Whisper at real-time factor <1, send that one job to a faster path (a beefier machine, or a cloud STT). Urgency and device capability — not a global switch — pick the engine per job.
- This makes a **queue** the unifying primitive: the same offline/backlog queue that survives dead zones is also where non-urgent local transcription lives; drain it on idle, escalate the head of the line when something is urgent.
