#!/usr/bin/env python3
"""Local tokens against cloud tokens, two ways. Decide nothing silently: print both.

    python3 tools/ledger.py [--session REC.jsonl ...] [--build REC.jsonl ...] [--since ISO-TIME]

LOCAL            prompt + completion tokens over local/local_usage.jsonl (cached prompt tokens count,
                 as cloud cache reads count).
CLOUD, the run   local/cloud_usage.jsonl, plus the assistant messages in each --session record sent while
                 the run was going (from the first to the last local or cloud call).
CLOUD, all       the run, plus every message in each --build record (the session that built the pipeline;
                 --since drops its messages before a moment). Claude Code keeps records under
                 ~/.claude/projects/<project>/<session>.jsonl, subagents in <session>/subagents/.
Session messages are counted once by message id, keeping the largest value of each usage field (a streamed
message is logged several times). Stdlib only; nothing here calls a model.
"""
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

L = Path(__file__).resolve().parent.parent / "local"
KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")

def rows(p):
    if not Path(p).exists(): return
    for line in open(p, errors="replace"):
        try: yield json.loads(line)
        except ValueError: pass

def messages(paths, since=None, until=None):
    seen = {}
    for p in paths:
        for d in rows(p):
            m, ts = d.get("message"), d.get("timestamp") or ""
            if d.get("type") != "assistant" or not isinstance(m, dict) or not m.get("id") or not m.get("usage"): continue
            if (since and ts < since) or (until and ts > until): continue
            prev = seen.get(m["id"], {})
            seen[m["id"]] = {k: max(m["usage"].get(k) or 0, prev.get(k) or 0) for k in KEYS}
    return seen

ap = argparse.ArgumentParser(); ap.add_argument("--session", nargs="*", default=[]); ap.add_argument("--build", nargs="*", default=[]); ap.add_argument("--since")
a = ap.parse_args()
loc = list(rows(L / "local_usage.jsonl")); cl = list(rows(L / "cloud_usage.jsonl"))
LOCAL = sum((r.get("prompt_tokens") or 0) + (r.get("completion_tokens") or 0) for r in loc)
ONESHOT = sum(r.get("total") or 0 for r in cl)
# local logs carry local time with an offset, session records carry UTC "Z" times: compare in UTC
utc = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
ts = sorted(utc(r["ts"]) for r in loc + cl if r.get("ts"))
during = messages(a.session, ts[0], ts[-1] + "~") if ts and a.session else {}
build = messages(a.build, utc(a.since) if a.since else None)
RUN = ONESHOT + sum(sum(v.values()) for v in during.values())
ALL = ONESHOT + sum(sum(v.values()) for v in (build | during).values())
share = lambda c: 100 * LOCAL / (LOCAL + c) if LOCAL + c else 0
print(f"LOCAL                        {LOCAL:>13,}   ({len(loc)} calls)")
print(f"CLOUD one-shot calls         {ONESHOT:>13,}   ({len(cl)} calls)")
print(f"CLOUD session, during run    {RUN - ONESHOT:>13,}   ({len(during)} messages)")
print(f"CLOUD build session(s)       {ALL - RUN:>13,}   ({len(set(build) - set(during))} more messages)")
print(f"local share, the run         {share(RUN):>12.1f}%   (local / (local + run cloud))")
print(f"local share, everything      {share(ALL):>12.1f}%   (local / (local + all cloud))")
