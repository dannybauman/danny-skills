#!/usr/bin/env bash
# The local run's one entry point (references/local-first.md). Every unit writes its result and done-marker
# atomically, so any stop, a crash included, resumes where it left off.
#   tools/run.sh [start]                 start, or resume (runs detached in its own session; log: local/run.log)
#   tools/run.sh pause                   stop after the local call in flight; the model is unloaded (touch local/PAUSE does the same)
#   tools/run.sh status                  local/STATUS.txt and whether the run is alive; loads no model
#   tools/run.sh pause-at HH:MM          pause at a clock time today (run it with nohup ... &)
#   tools/run.sh resume-when-free [PCT]  wait until memory free >= PCT (default 42), then resume; touch local/WAIT_CANCEL stops the wait
# The work itself is local/pipeline.sh (or $PIPELINE): `step <id> <text|vision|path.gguf|-> <command ...>` lines, plus any shell around them.
# SIGINT and SIGTERM to the run behave as pause.
cd "$(dirname "$0")/.." || exit 1
mkdir -p local
running() { [ -f local/run.pid ] && kill -0 "$(cat local/run.pid)" 2>/dev/null && ps -p "$(cat local/run.pid)" -o command= | grep -q 'run.sh _run'; }
step() {   # one unit; a pause (exit 75) stops the whole run, a failure is reported and returned
  [ -f "local/units/$1.done" ] && return 0
  [ -f local/PAUSE ] && { echo "paused before: $1"; exit 75; }
  echo "== $(date +%H:%M:%S) $1"
  python3 tools/local.py unit "$1" "$2" -- "${@:3}" & local c=$! rc=0
  wait $c; rc=$?
  while kill -0 $c 2>/dev/null; do wait $c; rc=$?; done   # a trapped signal interrupts wait; keep waiting for the unit itself
  [ $rc -eq 75 ] && { echo "paused during: $1 (tools/run.sh resumes it)"; exit 75; }
  [ $rc -eq 0 ] || echo "FAILED ($rc): $1"
  return $rc
}
case "${1:-start}" in
  start)
    if running; then echo "already running (pid $(cat local/run.pid))"; exit 0; fi
    rm -f local/PAUSE local/DONE
    python3 tools/local.py stop          # a model server left by a killed run
    python3 tools/local.py launch > local/run.pid
    echo "running (pid $(cat local/run.pid)); progress: tools/run.sh status or local/STATUS.txt; stop: tools/run.sh pause" ;;
  pause) touch local/PAUSE
    if running; then echo "pause requested: it stops after the call in flight (local/DONE appears when it has)"; else echo "not running (PAUSE is set; tools/run.sh clears it)"; fi ;;
  status) cat local/STATUS.txt 2>/dev/null || echo "no run yet"
    if running; then echo "process      running (pid $(cat local/run.pid))"; else echo "process      stopped$([ -f local/DONE ] && echo "; $(cat local/DONE)")"; fi ;;
  pause-at) at="${2:?usage: tools/run.sh pause-at HH:MM}"
    target=$(date -j -f "%Y-%m-%d %H:%M" "$(date +%Y-%m-%d) $at" +%s 2>/dev/null || date -d "$at" +%s) || exit 2
    [ "$target" -gt "$(date +%s)" ] && sleep $((target - $(date +%s)))
    touch local/PAUSE; echo "$(date +%H:%M:%S) pause-at $at: pause requested" >> local/run.log
    for _ in $(seq 1 60); do running || { echo "$(date +%H:%M:%S) pause-at: stopped cleanly" >> local/run.log; exit 0; }; sleep 5; done
    echo "$(date +%H:%M:%S) pause-at: still running after 5 min; stopping it" >> local/run.log
    kill -TERM -- "-$(cat local/run.pid)" 2>/dev/null; sleep 10; kill -KILL -- "-$(cat local/run.pid)" 2>/dev/null
    python3 tools/local.py stop; python3 tools/local.py note "stopped by pause-at $at after a 5 minute grace" ;;
  resume-when-free) want="${2:-42}"   # a little over the 40% load guard
    while f=$(python3 tools/local.py free); [ "$f" -lt "$want" ]; do
      [ -f local/WAIT_CANCEL ] && { rm -f local/WAIT_CANCEL; echo "$(date +%H:%M:%S) wait cancelled" >> local/run.log; exit 0; }
      echo "$(date +%H:%M:%S) waiting to resume: memory free $f% (need $want%)" >> local/run.log; sleep 60
    done
    echo "$(date +%H:%M:%S) memory free $f%: resuming" >> local/run.log; exec "$0" start ;;
  _run)
    trap 'rc=$?; python3 tools/local.py stop; python3 tools/local.py note "$(case $rc in 0) echo finished;; 75) echo "paused (tools/run.sh resumes)";; *) echo "failed (exit $rc; see local/run.log)";; esac)"; echo "exit $rc at $(date +%H:%M:%S)" > local/DONE' EXIT
    trap 'touch local/PAUSE; echo "[pause] signal: stopping after the call in flight"' INT TERM
    export HF_HUB_OFFLINE=1
    echo "== $(date '+%Y-%m-%d %H:%M:%S') run starts"
    # shellcheck disable=SC1090
    . "${PIPELINE:-local/pipeline.sh}" ;;
  *) echo "usage: tools/run.sh [start|pause|status|pause-at HH:MM|resume-when-free [PCT]]"; exit 2 ;;
esac
