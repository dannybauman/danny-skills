#!/usr/bin/env bash
# Local-model capability probe.
#
# Classifies a local LLM endpoint into three rungs:
#   rung 1 — reachable: server answers and lists models
#   rung 2 — completion: a single-shot chat completion returns real text
#   rung 3 — tool-capable: the model emits a STRUCTURED tool_calls object
#            (not a prose description) — the prerequisite for agentic use
#
# Speaks the OpenAI-compatible wire format (/v1). LM Studio is OpenAI-compatible;
# Ollama also exposes /v1 alongside its native API.
#
# Usage:
#   probe.sh                                   # auto-detect LM Studio :1234 + Ollama :11434
#   probe.sh --url http://localhost:1234/v1    # probe one endpoint (first model auto-picked)
#   probe.sh --url http://localhost:1234/v1 --model qwen3.5-9b
#
# Exit code: 0 = probe completed (highest rung reached is reported in the
# output; parse the "highest rung reached:" line to gate scripted use),
# 2 = usage error.
set -uo pipefail

URL=""
MODEL=""
while [ $# -gt 0 ]; do
  case "$1" in
    --url) URL="${2:-}"; shift 2 ;;
    --model) MODEL="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then echo "python3 required" >&2; exit 2; fi

# Highest rung reached across all probed endpoints (for the exit code).
BEST=0

# probe_endpoint <base-url> <model-or-empty>
probe_endpoint() {
  local base="$1" model="$2"
  base="${base%/}"
  echo "── $base"

  # Rung 1: reachable + models. Distinguish "server down" (curl failed) from
  # "server up but zero models loaded" (valid JSON, empty list).
  local models_json curl_rc
  models_json="$(curl -sS --max-time 8 "$base/models" 2>/dev/null)"; curl_rc=$?
  local first_model
  first_model="$(printf '%s' "$models_json" | "$PY" -c '
import json,sys
try: d=json.load(sys.stdin)
except Exception: print("NOJSON"); sys.exit(0)
ids=[m.get("id") for m in d.get("data",[]) if m.get("id")]
print("OK" if ids else "EMPTY")
print(ids[0] if ids else "")
print("|".join(ids[:8]))
' 2>/dev/null)"
  local status picked listing
  status="$(printf '%s' "$first_model" | sed -n '1p')"
  picked="$(printf '%s' "$first_model" | sed -n '2p')"
  listing="$(printf '%s' "$first_model" | sed -n '3p')"
  if [ "$curl_rc" -ne 0 ]; then
    echo "   rung 1 ✗  not reachable (server not answering at $base/models)"
    return
  fi
  if [ "$status" != "OK" ]; then
    if [ "$status" = "EMPTY" ]; then
      echo "   rung 1 ✓  reachable — but ZERO models loaded; load one (lms load <model> / ollama pull <model>) and re-run"
      [ "$BEST" -lt 1 ] && BEST=1
    else
      echo "   rung 1 ✗  reachable but not an OpenAI-compatible endpoint (non-JSON response at $base/models)"
    fi
    return
  fi
  echo "   rung 1 ✓  reachable — models: ${listing//|/, }"
  [ "$BEST" -lt 1 ] && BEST=1
  [ -z "$model" ] && model="$picked"
  echo "   model:   $model"

  # Rung 2: single-shot completion.
  local comp
  comp="$(curl -sS --max-time 90 "$base/chat/completions" \
    -H 'content-type: application/json' \
    -d "$("$PY" -c 'import json,sys; print(json.dumps({"model":sys.argv[1],"messages":[{"role":"user","content":"Reply with the single word: ready"}],"max_tokens":4000,"temperature":0}))' "$model")" 2>/dev/null)" || true
  local text
  text="$(printf '%s' "$comp" | "$PY" -c '
import json,sys
try: d=json.load(sys.stdin)
except Exception: print(""); sys.exit(0)
try: print((d["choices"][0]["message"].get("content") or "").strip().replace("\n"," ")[:60])
except Exception: print("")
' 2>/dev/null)"
  if [ -z "$text" ]; then
    echo "   rung 2 ✗  no completion text (server down, model not loaded, or all tokens spent on reasoning)"
    return
  fi
  echo "   rung 2 ✓  completion works — \"$text\""
  [ "$BEST" -lt 2 ] && BEST=2

  # Rung 3: structured tool-calling. Ask for a tool and inspect whether the model
  # returns a real tool_calls object vs describing the call in prose.
  local toolreq
  toolreq="$("$PY" -c '
import json,sys
print(json.dumps({
  "model": sys.argv[1],
  "messages": [{"role":"user","content":"What is the weather in Paris? Use the get_weather tool."}],
  "tools": [{"type":"function","function":{
    "name":"get_weather",
    "description":"Get current weather for a city",
    "parameters":{"type":"object","properties":{"city":{"type":"string"}},"required":["city"]}}}],
  "tool_choice": "auto",
  "max_tokens": 4000,
  "temperature": 0
}))' "$model")"
  local toolresp
  toolresp="$(curl -sS --max-time 90 "$base/chat/completions" -H 'content-type: application/json' -d "$toolreq" 2>/dev/null)" || true
  local verdict
  verdict="$(printf '%s' "$toolresp" | "$PY" -c '
import json,sys
try: d=json.load(sys.stdin)
except Exception: print("err"); sys.exit(0)
try:
    msg=d["choices"][0]["message"]
    tc=msg.get("tool_calls")
    if tc and len(tc)>0 and tc[0].get("function",{}).get("name"):
        print("structured:"+tc[0]["function"]["name"])
    else:
        print("textonly")
except Exception:
    print("err")
' 2>/dev/null)"
  case "$verdict" in
    structured:*)
      echo "   rung 3 ✓  emits structured tool_calls (${verdict#structured:}) — agentic-capable"
      [ "$BEST" -lt 3 ] && BEST=3
      ;;
    textonly)
      echo "   rung 3 ✗  no structured tool_calls — model describes tools as text, NOT agentic-safe"
      ;;
    *)
      echo "   rung 3 ?  tool probe returned no parseable response"
      ;;
  esac
}

if [ -n "$URL" ]; then
  probe_endpoint "$URL" "$MODEL"
else
  echo "auto-detecting local endpoints…"
  probe_endpoint "http://localhost:1234/v1" "$MODEL"   # LM Studio
  probe_endpoint "http://localhost:11434/v1" "$MODEL"  # Ollama (OpenAI-compatible)
fi

echo ""
echo "highest rung reached: $BEST  (1=reachable 2=completion 3=tool-capable)"
echo "→ rung 2 is enough for COMPLETION work; AGENTIC work needs rung 3."
exit 0
