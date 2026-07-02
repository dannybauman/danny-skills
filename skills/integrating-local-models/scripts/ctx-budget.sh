#!/usr/bin/env bash
# ctx-budget.sh — preflight a local agentic step BEFORE you run it, so you route a
# too-heavy step to the cloud instead of discovering the wall by swap-thrashing.
#
# The lesson it encodes (measured on a 16GB M1): a 72K-char source
# forced ~41K prompt tokens → ≥48K ctx → model + f16 KV cache overcommitted 16GB →
# 15GB swap, zero output. Knowable in advance from input size + RAM.
#
#   bash ctx-budget.sh --source-chars 72000              # detects RAM; assumes a 9B
#   bash ctx-budget.sh --source-chars 12000 --ram-gb 16 --model-gb 6.5
#
# Heuristic, not exact — KV math is approximated from measured 9B@Q4 data points in
# SKILL.md (~42MB/1K tok f16, ~half at q8_0). Verdict is conservative on purpose.
set -euo pipefail
export LC_NUMERIC=C

SRC_CHARS=0; RAM_GB=""; MODEL_GB=6.5; BASE_PROMPT_TOK=23000   # opencode base ~23K (SKILL.md)
# LM Studio allocates the full --context-length PER parallel slot, so total KV ≈ ctx ×
# n_parallel. Its default is often 4 → 4× the KV for zero benefit to a single agentic
# run. Measured on a 16GB M1: reloading 32K@parallel-4 → 48K@parallel-1 LOWERED
# resident RAM (free mem rose) AND gave the one run the full window. Default 1 here; pass
# --parallel 4 to model what a default LM Studio JIT load actually costs.
PARALLEL=1
# Reserve for OS + a REAL working desktop (browser + editor + the app's own dev server +
# your agent). Empirically ~7GB: a ~9GB-resident 9B@64K tipped a loaded 16GB M1 into 15GB
# swap (measured). An idle machine could use less (--apps-reserve 4).
APPS_RESERVE=7
while [ $# -gt 0 ]; do case "$1" in
  --source-chars)
    if [ $# -lt 2 ]; then echo "Error: --source-chars requires a value" >&2; exit 2; fi
    SRC_CHARS="$2"; shift 2;;
  --ram-gb)
    if [ $# -lt 2 ]; then echo "Error: --ram-gb requires a value" >&2; exit 2; fi
    RAM_GB="$2"; shift 2;;
  --model-gb)
    if [ $# -lt 2 ]; then echo "Error: --model-gb requires a value" >&2; exit 2; fi
    MODEL_GB="$2"; shift 2;;
  --base-prompt-tok)
    if [ $# -lt 2 ]; then echo "Error: --base-prompt-tok requires a value" >&2; exit 2; fi
    BASE_PROMPT_TOK="$2"; shift 2;;
  --apps-reserve)
    if [ $# -lt 2 ]; then echo "Error: --apps-reserve requires a value" >&2; exit 2; fi
    APPS_RESERVE="$2"; shift 2;;
  --parallel)
    if [ $# -lt 2 ]; then echo "Error: --parallel requires a value" >&2; exit 2; fi
    PARALLEL="$2"; shift 2;;
  *) echo "unknown arg: $1" >&2; exit 2;;
esac; done

# Detect RAM (macOS) if not given.
if [ -z "$RAM_GB" ]; then
  RAM_GB=$(sysctl -n hw.memsize 2>/dev/null | awk '{printf "%.0f", $1/1024/1024/1024}') || RAM_GB=16
fi

if [ -z "$RAM_GB" ] || [ "$RAM_GB" -eq 0 ] 2>/dev/null; then
  RAM_GB=16
fi

# chars→tokens ≈ /4; prompt = base + source; +30% headroom for output + tool-loop growth.
src_tok=$(( SRC_CHARS / 4 ))
prompt_tok=$(( BASE_PROMPT_TOK + src_tok ))
need_ctx=$(awk -v p="$prompt_tok" 'BEGIN{printf "%d", p*1.3}')
# Round up to a sane loadable context.
ctx=8192; for c in 8192 16384 32768 49152 65536 98304 131072; do if [ "$need_ctx" -le "$c" ]; then ctx=$c; break; fi; ctx=$c; done

# KV scales with total allocated context = ctx × n_parallel (LM Studio gives each slot
# the full ctx). A default parallel-4 load quadruples this — the silent footgun.
kv_f16=$(awk -v c="$ctx" -v n="$PARALLEL" 'BEGIN{printf "%.1f", c/1024*0.042*n}')   # GB
kv_q8=$(awk -v c="$ctx"  -v n="$PARALLEL" 'BEGIN{printf "%.1f", c/1024*0.021*n}')
res_f16=$(awk -v m="$MODEL_GB" -v k="$kv_f16" 'BEGIN{printf "%.1f", m+k}')
res_q8=$(awk -v m="$MODEL_GB" -v k="$kv_q8"  'BEGIN{printf "%.1f", m+k}')
safe=$(awk -v r="$RAM_GB" -v a="$APPS_RESERVE" 'BEGIN{printf "%.1f", r-a}')   # leave room for OS + working apps

echo "input:        ${SRC_CHARS} chars (~${src_tok} tok) + ${BASE_PROMPT_TOK} base = ~${prompt_tok} prompt tok"
echo "required ctx:  ~${need_ctx} tok  → load at ${ctx} (--parallel ${PARALLEL}: KV ×${PARALLEL})"
echo "resident RAM:  f16 KV ${res_f16}GB | q8_0 KV ${res_q8}GB   (safe budget on ${RAM_GB}GB ≈ ${safe}GB, after ${APPS_RESERVE}GB OS+apps)"
if [ "$PARALLEL" -gt 1 ] 2>/dev/null; then
  echo "note:         parallel=${PARALLEL} multiplies KV — a single agentic run only needs 1. Load with --parallel 1 to reclaim KV and give the run the full window."
fi

verdict() { awk -v a="$1" -v b="$2" 'BEGIN{exit !(a<=b)}'; }
if verdict "$res_f16" "$safe"; then
  echo "VERDICT: LOCAL-SAFE — lms load <model> --context-length ${ctx} --parallel 1; FlashAttention recommended for prefill."
elif verdict "$res_q8" "$safe"; then
  echo "VERDICT: LOCAL-WITH-LEVERS — needs FlashAttention + KV q8_0 (--cache-type-k q8_0 --cache-type-v q8_0) to fit; set enable_thinking=false to shrink the prompt."
else
  echo "VERDICT: ROUTE-TO-CLOUD — even q8_0 KV (${res_q8}GB) exceeds the ${safe}GB budget. This step belongs on a big-context cloud agent (claude-code). Don't thrash it locally."
fi
