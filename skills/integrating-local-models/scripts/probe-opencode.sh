#!/usr/bin/env bash
# End-to-end opencode tool-EXECUTION probe — the "sufficient" rung-3 test.
#
# probe.sh checks whether a model EMITS structured tool_calls (necessary). This
# script checks whether opencode actually EXECUTES them end-to-end (sufficient):
# it drives a real `opencode run` against a throwaway git repo with a trivial
# agentic task — write a file, edit it, git-commit it — then VERIFIES the file
# landed on disk AND the commit happened. Tool-calls-printed-as-text = FAIL.
# Real file + real commit = PASS. That is the only bar that matters for agentic.
#
# WHY this exists beyond probe.sh: a weak local model behind opencode "describes"
# Read/Write/Edit/Bash instead of running them — silent wrong output (no files,
# no commit). Verified models differ: qwen3.5-9b PASSes; qwen2.5-coder emits
# tool-calls as a JSON text block and FAILs even at full context.
#
# PREREQUISITES (or this fails for the wrong reason):
#   1. The model is REGISTERED in ~/.config/opencode/opencode.json under
#      provider.<id>.models with tools:true. opencode's `opencode models` is a
#      stale CATALOG, not your installed list — an unregistered id throws
#      ProviderModelNotFoundError.
#   2. The model is loaded with context >= ~48K (64K safe). opencode's base prompt
#      is ~23K (n_keep ~22803), but a REAL agentic step (step template + injected
#      source) is bigger — a portal express run measured ~36K (n_keep 35714), so
#      32K overflows on real work. LM Studio ERRORS on overflow; Ollama SILENTLY
#      TRUNCATES to its 4K default, stripping the tool instructions so the model
#      falls back to text. Load big:
#        LM Studio:  lms load <model> --context-length 65536 --parallel 1
#                    (--parallel 1 matters: LM Studio allocates the full ctx PER slot,
#                    so its default parallel-4 quadruples KV for no single-run benefit.)
#        Ollama:     create a Modelfile tag (FROM <m>\nPARAMETER num_ctx 65536),
#                    then `ollama create <m>-64k -f Modelfile`  (the opencode
#                    catalog's `:7b-32k` suffix is NOT a real ollama tag).
#   3. SERIAL ONLY. opencode boots a server per run and swaps process.env
#      globally — never run two probes at once.
#   4. On a 16GB-class machine, load ONE model at a time (two models, or LM
#      Studio + Ollama both resident, thrashes swap and can lock the machine).
#
# Usage:
#   probe-opencode.sh --model lmstudio/qwen3.5-9b
#   probe-opencode.sh --model ollama/qwen2.5-coder:7b-32k --keep   # keep temp repo
#
# Exit code: 0 = PASS (file + commit verified on disk), 1 = FAIL.
set -uo pipefail

MODEL=""
KEEP=0
while [ $# -gt 0 ]; do
  case "$1" in
    --model) MODEL="${2:-}"; shift 2 ;;
    --keep) KEEP=1; shift ;;
    -h|--help) sed -n '2,40p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$MODEL" ]; then echo "required: --model <provider/model>" >&2; exit 2; fi
command -v opencode >/dev/null 2>&1 || { echo "opencode not on PATH" >&2; exit 2; }

WORK="$(mktemp -d "${TMPDIR:-/tmp}/opencode-probe.XXXXXX")"
cleanup() { [ "$KEEP" -eq 1 ] && echo "kept: $WORK" || rm -rf "$WORK"; }
trap cleanup EXIT

(
  cd "$WORK" || exit 2
  git init -q
  git config user.email probe@local
  git config user.name probe
  echo init > README.md
  git add README.md
  git commit -qm init
)

echo "── opencode tool-execution probe"
echo "   model: $MODEL"
echo "   repo:  $WORK"

TASK="Use your tools to do exactly this in the current directory. Do NOT just \
describe the steps - actually call the tools. 1) Create a file named probe.txt \
whose contents are the single line: BANANA  2) Edit probe.txt to append a second \
line: SPLIT  3) Run a bash command: git add probe.txt && git commit -m 'probe: \
rung-3 tool execution'. After committing, reply DONE."

TIMEOUT_CMD=""
if command -v timeout >/dev/null 2>&1; then
  TIMEOUT_CMD="timeout"
elif command -v gtimeout >/dev/null 2>&1; then
  TIMEOUT_CMD="gtimeout"
fi

if [ -n "$TIMEOUT_CMD" ]; then
  ( cd "$WORK" && $TIMEOUT_CMD 420 opencode run --model "$MODEL" --log-level ERROR "$TASK" ) \
    >/dev/null 2>&1 || true
else
  ( cd "$WORK" && opencode run --model "$MODEL" --log-level ERROR "$TASK" ) \
    >/dev/null 2>&1 || true
fi

# Verdict is decided ONLY by on-disk state, never by what opencode printed.
FILE_OK=0; COMMIT_OK=0
if [ -f "$WORK/probe.txt" ] \
  && grep -q BANANA "$WORK/probe.txt" \
  && grep -q SPLIT "$WORK/probe.txt"; then FILE_OK=1; fi
if ( cd "$WORK" && git log --oneline 2>/dev/null | grep -q "rung-3 tool execution" ); then COMMIT_OK=1; fi

echo "   file written (BANANA+SPLIT): $([ "$FILE_OK" -eq 1 ] && echo '✓' || echo '✗')"
echo "   commit landed:               $([ "$COMMIT_OK" -eq 1 ] && echo '✓' || echo '✗')"
echo ""
if [ "$FILE_OK" -eq 1 ] && [ "$COMMIT_OK" -eq 1 ]; then
  echo "RUNG-3 PASS — opencode executed tools with $MODEL (real file + commit)."
  exit 0
fi
echo "RUNG-3 FAIL — $MODEL did not execute tools (tool-calls-as-text, or a"
echo "prerequisite is unmet: model not registered, or context < ~32K). See header."
exit 1
