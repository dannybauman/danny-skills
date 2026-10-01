#!/usr/bin/env python3
"""One cloud call, nothing kept open, its token usage appended to local/cloud_usage.jsonl.

    python3 tools/cloud.py <task> [--system TEXT] [--model sonnet] < prompt     (prints the reply)

Runs `claude -p` from an empty temporary folder with no tools, no MCP servers, no slash commands and a short
system prompt. That shape measured 33,600 tokens for a trivial prompt on a subscription login, against 78,300
for a default `claude -p`. `--bare` would be leaner but needs an API key ("Not logged in" on a subscription).
Stdlib only.
"""
import argparse, json, subprocess, sys, tempfile
from datetime import datetime
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "local" / "cloud_usage.jsonl"
ap = argparse.ArgumentParser(); ap.add_argument("task"); ap.add_argument("--model", default="sonnet")
ap.add_argument("--system", default="You answer one request. Reply with only what is asked for, no preamble.")
a = ap.parse_args(); prompt = sys.stdin.read()
with tempfile.TemporaryDirectory(prefix="cloud-call-") as empty:   # an empty folder: no project files or instructions to load
    p = subprocess.run(["claude", "-p", prompt, "--output-format", "json", "--model", a.model, "--disable-slash-commands", "--strict-mcp-config",
                        "--tools", "", "--system-prompt", a.system, "--setting-sources", "project"], cwd=empty, capture_output=True, text=True)
try: d = json.loads(p.stdout)
except ValueError: sys.exit(f"claude -p did not return JSON (exit {p.returncode}): {(p.stderr or p.stdout)[:300]}")
u = d.get("usage") or {}
LOG.parent.mkdir(exist_ok=True)
with open(LOG, "a") as f:
    f.write(json.dumps({"ts": datetime.now().astimezone().isoformat(timespec="seconds"), "task": a.task, "model": a.model, "usage": u,
                        "total": sum(u.get(k) or 0 for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")),
                        "cost_usd": d.get("total_cost_usd"), "error": d.get("is_error")}) + "\n")
if d.get("is_error"): sys.exit(f"cloud call failed: {str(d.get('result'))[:300]}")
print(d.get("result", ""))
