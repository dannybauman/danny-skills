#!/usr/bin/env bash
# Prove the local-first driver without any model: a stub server answers in place of llama-server, and six fake
# units of two calls each are paused, signalled, hard-killed and resumed. Checks that finished units are never
# redone, the interrupted one is, the "model" is unloaded on every stop, and a killed run's server is cleaned up.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"; trap 'pkill -f "$tmp/stub.py" 2>/dev/null || true; rm -rf "${tmp:?}"' EXIT
p="$tmp/p"; mkdir -p "$p"; cp -R "$here/starter/." "$p/"; cd "$p"
cat > "$tmp/stub.py" <<'PY'
import json, sys, time
from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def reply(self, d):
        b = json.dumps(d).encode(); self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self): self.reply({"status": "ok"})
    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"])); time.sleep(0.6)
        self.reply({"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 100, "completion_tokens": 10}, "timings": {"cache_n": 90}})
HTTPServer(("127.0.0.1", int(sys.argv[sys.argv.index("--port") + 1])), H).serve_forever()
PY
cat > local/unit.sh <<'SH'
set -e
a=$(echo "first part of $UNIT_ID" | python3 tools/local.py ask "$UNIT_ID-a")
b=$(echo "second part of $UNIT_ID" | python3 tools/local.py ask "$UNIT_ID-b")
echo "$a $b" > "$UNIT_OUT"
SH
printf 'for u in u1 u2 u3 u4 u5 u6; do step "$u" text bash local/unit.sh || exit 1; done\n' > local/pipeline.sh
touch "$tmp/fake-model.gguf"
port=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
export LLAMA_SERVER="python3 $tmp/stub.py" LOCAL_TEXT_MODEL="$tmp/fake-model.gguf" LOCAL_PORT="$port" LOCAL_MIN_FREE=0 LOCAL_MIN_DISK=0 LOCAL_PAUSE_FREE=0

fail() { echo "FAIL: $*"; tail -5 local/run.log 2>/dev/null; exit 1; }
waitfor() { for _ in $(seq 1 300); do eval "$1" && return 0; sleep 0.1; done; fail "timed out waiting for: $1"; }
stopped() { [ -f local/DONE ] && grep -q "exit $1" local/DONE || fail "expected the run to stop with exit $1, got: $(cat local/DONE 2>/dev/null)"; }
unloaded() { [ ! -f local/llama.pid ] && ! pgrep -f "$tmp/stub.py" >/dev/null || fail "the model server is still loaded after a stop"; }
ndone() { ls local/units/*.done 2>/dev/null | wc -l | tr -d ' '; }
calls() { grep -c "\"task\": \"$1\"" local/local_usage.jsonl || true; }
t0=$(date +%s)

tools/run.sh >/dev/null; waitfor '[ -f local/units/u1.done ]'; tools/run.sh pause >/dev/null; waitfor '[ -f local/DONE ]'
stopped 75; unloaded; [ "$(ndone)" -lt 6 ] || fail "pause did not stop the run"; grep -q paused local/STATUS.txt || fail "STATUS.txt does not say paused"
echo "ok   pause: stopped after the call in flight with $(ndone) of 6 units done; model unloaded"
tools/run.sh status >/dev/null; [ ! -f local/llama.pid ] || fail "status loaded a model"
sleep 2

tools/run.sh >/dev/null; waitfor '[ -f local/units/u3.done ]'; kill -TERM "$(cat local/run.pid)"; waitfor '[ -f local/DONE ]'
stopped 75; unloaded; [ "$(ndone)" -lt 6 ] || fail "SIGTERM did not stop the run"
echo "ok   SIGTERM: behaved as pause with $(ndone) of 6 done; model unloaded"
sleep 2

tools/run.sh >/dev/null; waitfor 'grep -q "\"u5-a\"" local/local_usage.jsonl'; stale=$(python3 -c 'import json; print(json.load(open("local/llama.pid"))["pid"])')
kill -KILL -- "-$(cat local/run.pid)"; sleep 0.5
kill -0 "$stale" 2>/dev/null || fail "test setup: the stub server should have outlived the killed run"
echo "ok   hard kill: run gone mid-unit, its model server left behind (pid $stale)"

tools/run.sh >/dev/null; kill -0 "$stale" 2>/dev/null && fail "start did not stop the stale model server"
waitfor '[ -f local/DONE ]'; stopped 0; unloaded
[ "$(ndone)" = 6 ] || fail "expected 6 units done, got $(ndone)"
for u in u1 u2 u3 u4; do [ "$(calls "$u-b")" = 1 ] || fail "finished unit $u was asked again ($(calls "$u-b") times)"; done
[ "$(calls u5-a)" -ge 2 ] || fail "u5, killed part way, should have been redone from its start"
for u in u1 u2 u3 u4 u5 u6; do [ "$(cat "local/units/$u.out")" = "ok ok" ] || fail "result for $u missing or wrong"; done
grep -q '^state        finished' local/STATUS.txt || fail "STATUS.txt does not say finished"
echo "ok   resume: stale server cleaned up, all 6 done, finished units never redone, the killed unit redone"

wall=$(( $(date +%s) - t0 )); run=$(python3 tools/local.py elapsed)
[ "$run" -lt $((wall - 3)) ] || fail "running time ($run s) should leave out the paused gaps (wall $wall s)"
echo "ok   running time $run s of $wall s wall: paused time is not counted"
mkdir -p "$tmp/bin"; printf '%s\n' '#!/bin/sh' '[ -z "$(ls -A .)" ] || { echo "{\"is_error\": true, \"result\": \"not run from an empty folder\"}"; exit 0; }' \
  'echo "{\"is_error\": false, \"result\": \"stub reply\", \"usage\": {\"input_tokens\": 3, \"output_tokens\": 5, \"cache_creation_input_tokens\": 1000, \"cache_read_input_tokens\": 2000}}"' > "$tmp/bin/claude"
chmod +x "$tmp/bin/claude"
[ "$(echo hi | PATH="$tmp/bin:$PATH" python3 tools/cloud.py check)" = "stub reply" ] || fail "cloud.py did not return the reply"
grep -q '"total": 3008' local/cloud_usage.jsonl || fail "cloud.py did not log usage"
python3 - "$tmp/session.jsonl" <<'PY2'
import json, sys
from datetime import datetime, timedelta, timezone
now = (datetime.now(timezone.utc) - timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
msg = lambda i, ts, out: json.dumps({"type": "assistant", "timestamp": ts, "message": {"id": i, "usage": {"input_tokens": 10, "output_tokens": out}}})
open(sys.argv[1], "w").write("\n".join([msg("during", now, 5), msg("during", now, 50), msg("before", "2000-01-01T00:00:00.000Z", 990)]) + "\n")
PY2
led=$(python3 tools/ledger.py --session "$tmp/session.jsonl" --build "$tmp/session.jsonl")
n=$(wc -l < local/local_usage.jsonl | tr -d ' ')
echo "$led" | grep -q "LOCAL  *$(python3 -c "print(f'{$n * 110:,}')") " || fail "ledger LOCAL is wrong: $led"
echo "$led" | grep -q "during run  *60 " || fail "ledger did not count the streamed session message once: $led"
echo "$led" | grep -q "build session(s)  *1,000 " || fail "ledger build view is wrong: $led"
echo "ok   cloud.py logs usage from an empty folder (stub claude); ledger counts each session message once, in both views"
echo "PASS: pause, SIGTERM, hard kill and resume, cloud logging and ledger, with no model or cloud call"
