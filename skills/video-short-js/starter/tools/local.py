#!/usr/bin/env python3
"""The local-model harness behind tools/run.sh: one llama-server at a time, memory and disk guards,
one logged completion per `ask`, and resumable units. See references/local-first.md.

    python3 tools/local.py ask <task> [--brief FILE] [--image F.jpg ...] [--max-tokens N] [--temperature T] [--seed N] < prompt
    python3 tools/local.py unit <id> <text|vision|path.gguf|-> -- <command ...>    (what `step` in run.sh calls)
    python3 tools/local.py stop | free | elapsed | note <state> | launch

Models come from LOCAL_TEXT_MODEL, LOCAL_VISION_MODEL + LOCAL_VISION_MMPROJ, or a path given as the model;
a vision model with no variables set is looked for the way tools/local_viewer.py does. Nothing is downloaded.
`ask` exits 75 when a pause is requested, before it sends anything; a unit command passes that on.
Guards (environment): LOCAL_MIN_FREE 40 (% memory free to load), LOCAL_MIN_DISK 3 (GB), LOCAL_PAUSE_FREE 8
(% under which calls wait). Server: LLAMA_SERVER (default llama-server), LOCAL_PORT 8091, LOCAL_CTX 16384.
Everything lives in local/: usage logs, units/<id>.done markers and <id>.out results, STATUS.txt, PAUSE. Stdlib only.
"""
import base64, json, os, re, shlex, shutil, signal, subprocess, sys, time, urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
L = ROOT / "local"
PAUSE, PIDF, USAGE, STATUS = L / "PAUSE", L / "llama.pid", L / "local_usage.jsonl", L / "STATUS.txt"
PORT = int(os.environ.get("LOCAL_PORT", "8091"))
BASE = f"http://127.0.0.1:{PORT}"                 # loopback only
env_num = lambda k, d: float(os.environ.get(k, d))

class Paused(Exception): pass

def awrite(p, s):                                 # temp file then rename: a kill never leaves half a file
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True); t = p.with_name(p.name + ".tmp"); t.write_text(s); os.replace(t, p)

def free_pct():
    if shutil.which("memory_pressure"):
        m = re.search(r"free percentage:\s*(\d+)%", subprocess.run(["memory_pressure"], capture_output=True, text=True).stdout)
        return int(m.group(1)) if m else 0
    mi = dict(l.split(":", 1) for l in open("/proc/meminfo"))
    return int(int(mi["MemAvailable"].split()[0]) * 100 / int(mi["MemTotal"].split()[0]))

def disk_gb():
    if shutil.which("diskutil"):                  # macOS: df counts purgeable space as free; the container figure is the honest one
        m = re.search(r"Container Free Space:.*\((\d+) Bytes\)", subprocess.run(["diskutil", "info", "/System/Volumes/Data"], capture_output=True, text=True).stdout)
        if m: return int(m.group(1)) / 1e9
    return shutil.disk_usage(ROOT).free / 1e9

def resolve_model(key):
    if key == "text":
        p = os.environ.get("LOCAL_TEXT_MODEL") or sys.exit("set LOCAL_TEXT_MODEL to a GGUF already on disk (this harness never downloads one)")
        return Path(p).expanduser(), None
    if key == "vision":
        if os.environ.get("LOCAL_VISION_MODEL"): return Path(os.environ["LOCAL_VISION_MODEL"]).expanduser(), Path(os.environ["LOCAL_VISION_MMPROJ"]).expanduser()
        sys.path.insert(0, str(Path(__file__).parent)); from local_viewer import find_model
        g, mm = find_model(); g or sys.exit("no vision GGUF with an mmproj found; set LOCAL_VISION_MODEL and LOCAL_VISION_MMPROJ")
        return g, mm
    return Path(key).expanduser(), None

def loaded():
    try: s = json.loads(PIDF.read_text())
    except Exception: return None
    cmd = subprocess.run(["ps", "-p", str(s["pid"]), "-o", "command="], capture_output=True, text=True).stdout
    return s if s["model"] in cmd else None       # the pid file names a server only while that process still holds that model

def stop():
    s = loaded()
    if s:
        for sig, wait in ((signal.SIGTERM, 5), (signal.SIGKILL, 2)):
            try: os.killpg(s["pid"], sig)
            except ProcessLookupError: break
            for _ in range(wait * 4):
                if not loaded(): break
                time.sleep(0.25)
        print(f"[local] unloaded {Path(s['model']).name}; memory free {free_pct()}%", flush=True)
    PIDF.unlink(missing_ok=True)

class Unsafe(Exception): pass

def ensure(key):
    gguf, mmproj = resolve_model(key)
    s = loaded()
    if s and s["model"] == str(gguf): return
    stop()
    server = shlex.split(os.environ.get("LLAMA_SERVER", "llama-server"))
    if Path(server[0]).name == "llama-server" and subprocess.run(["pgrep", "-x", "llama-server"], capture_output=True).returncode == 0:
        raise Unsafe("another llama-server is already running; refusing to load a second model")
    free, disk = free_pct(), disk_gb()
    print(f"[guard] before load: memory free {free}%, disk {disk:.1f} GB", flush=True)
    if free < env_num("LOCAL_MIN_FREE", 40) or disk < env_num("LOCAL_MIN_DISK", 3):
        raise Unsafe(f"unsafe to load {gguf.name}: memory free {free}% (want {env_num('LOCAL_MIN_FREE', 40):g}), disk {disk:.1f} GB (want {env_num('LOCAL_MIN_DISK', 3):g})")
    args = server + ["-m", str(gguf), "-c", os.environ.get("LOCAL_CTX", "16384"), "-ngl", "99", "--parallel", "1", "--host", "127.0.0.1", "--port", str(PORT),
                     "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0", "--no-webui", "--chat-template-kwargs", '{"enable_thinking":false}'] + (["--mmproj", str(mmproj)] if mmproj else [])
    p = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=open(L / "llama.log", "w"), stderr=subprocess.STDOUT, start_new_session=True)
    awrite(PIDF, json.dumps({"pid": p.pid, "model": str(gguf), "port": PORT}))
    t0 = time.time()
    while True:                                   # wait on the server's own readiness signal
        try:
            if json.load(urllib.request.urlopen(BASE + "/health", timeout=2)).get("status") == "ok": break
        except Exception: pass
        if p.poll() is not None: raise Unsafe("the model server exited during load; see local/llama.log")
        if time.time() - t0 > 240: stop(); raise Unsafe("the model server was not ready after 240 s")
        time.sleep(1)
    print(f"[guard] {gguf.name} loaded in {time.time() - t0:.0f} s; memory free now {free_pct()}%", flush=True)

def ask(task, prompt, brief=None, images=(), max_tokens=1500, temperature=0.4, seed=None):
    if PAUSE.exists(): raise Paused(task)
    while (f := free_pct()) < env_num("LOCAL_PAUSE_FREE", 8):
        print(f"[guard] memory free {f}% is under the pause line: waiting 30 s", flush=True); time.sleep(30)
        if PAUSE.exists(): raise Paused(task)
    content = prompt if not images else [{"type": "text", "text": prompt}] + [
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(Path(i).read_bytes()).decode()}} for i in images]
    msgs = ([{"role": "system", "content": Path(brief).read_text()}] if brief else []) + [{"role": "user", "content": content}]
    body = {"model": "local", "messages": msgs, "max_tokens": max_tokens, "temperature": temperature, "top_p": 0.95, "cache_prompt": True,
            "chat_template_kwargs": {"enable_thinking": False}} | ({"seed": seed} if seed is not None else {})
    t0 = time.time()
    req = urllib.request.Request(os.environ.get("LOCAL_URL", BASE) + "/v1/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r: d = json.load(r)
    text = re.sub(r"<think>.*?</think>", "", (d.get("choices") or [{}])[0].get("message", {}).get("content") or "", flags=re.S).strip()
    u, tm, s = d.get("usage") or {}, d.get("timings") or {}, loaded() or {}
    rec = {"ts": datetime.now().astimezone().isoformat(timespec="seconds"), "model": Path(s.get("model", "?")).name, "task": task, "unit": os.environ.get("UNIT_ID"),
           "prompt_tokens": u.get("prompt_tokens"), "completion_tokens": u.get("completion_tokens"), "cached_tokens": tm.get("cache_n"),
           "tok_per_s": round(tm["predicted_per_second"], 1) if tm.get("predicted_per_second") else None, "seconds": round(time.time() - t0, 2),
           "finish": (d.get("choices") or [{}])[0].get("finish_reason")}
    with open(USAGE, "a") as f: f.write(json.dumps(rec) + "\n")
    return text

def elapsed():
    try: return float((L / "run_seconds").read_text())
    except Exception: return 0.0

def note(state, last=None):
    if last: awrite(L / "last", last)
    calls = toks = 0
    if USAGE.exists():
        for line in open(USAGE):
            try: r = json.loads(line); calls += 1; toks += (r.get("prompt_tokens") or 0) + (r.get("completion_tokens") or 0)
            except Exception: pass
    done, s = sorted((L / "units").glob("*.done")), loaded()
    awrite(STATUS, "\n".join([
        f"updated      {datetime.now():%Y-%m-%d %H:%M:%S}", f"state        {state}",
        f"last unit    {(L / 'last').read_text() if (L / 'last').exists() else '-'}",
        f"units done   {len(done)}" + (f" (latest: {', '.join(p.stem for p in sorted(done, key=lambda p: p.stat().st_mtime)[-3:])})" if done else ""),
        f"local        {toks:,} tokens in {calls} calls", f"running time {elapsed() / 3600:.2f} h (paused time not counted)",
        f"model        {Path(s['model']).name + ' loaded' if s else 'none loaded'}", f"machine      memory free {free_pct()}%, disk {disk_gb():.1f} GB", ""]))

def unit(uid, key, cmd):
    if not re.fullmatch(r"[A-Za-z0-9._-]+", uid): sys.exit(f"unit id must be letters, digits, . _ -: {uid}")
    # markers sit beside results in units/: on a case-insensitive disk (macOS default) a done/ folder
    # and the DONE file run.sh writes are the same name
    done, out = L / "units" / f"{uid}.done", L / "units" / f"{uid}.out"
    if done.exists(): return 0
    if PAUSE.exists(): return 75
    if key != "-":
        try: ensure(key)
        except Unsafe as e:
            print(f"[guard] {e}", flush=True); note(f"paused: {e} (tools/run.sh resume-when-free waits for memory)"); return 75
    def on_signal(n, _): PAUSE.touch(); print(f"[pause] signal {n}: stopping after the local call in flight", flush=True)
    signal.signal(signal.SIGINT, on_signal); signal.signal(signal.SIGTERM, on_signal)
    tmp = out.with_name(out.name + ".tmp"); tmp.parent.mkdir(parents=True, exist_ok=True); tmp.unlink(missing_ok=True)
    t0 = time.time()
    rc = subprocess.call(cmd, env=os.environ | {"UNIT_ID": uid, "UNIT_OUT": str(tmp), "LOCAL_URL": BASE})
    dt = time.time() - t0
    awrite(L / "run_seconds", f"{elapsed() + dt:.1f}")    # running time only: a cap on time since the first start would count every pause
    if rc == 0:
        if tmp.exists(): os.replace(tmp, out)
        awrite(done, json.dumps({"seconds": round(dt, 1), "at": datetime.now().astimezone().isoformat(timespec="seconds")}) + "\n")
    note("running", f"{uid} {'done' if rc == 0 else 'paused part way (redone on resume)' if rc == 75 else f'failed (exit {rc})'} after {dt:.0f} s")
    return rc

def main():
    a = sys.argv[1:] or ["-h"]; op = a[0]
    L.mkdir(exist_ok=True)
    if op == "ask":
        import argparse
        p = argparse.ArgumentParser(prog="local.py ask"); p.add_argument("task"); p.add_argument("--brief"); p.add_argument("--image", action="append", default=[])
        p.add_argument("--max-tokens", type=int, default=1500); p.add_argument("--temperature", type=float, default=0.4); p.add_argument("--seed", type=int)
        o = p.parse_args(a[1:])
        try: print(ask(o.task, sys.stdin.read(), o.brief, o.image, o.max_tokens, o.temperature, o.seed))
        except Paused: print(f"[pause] paused before {o.task}", file=sys.stderr); sys.exit(75)
    elif op == "unit":
        if len(a) < 5 or a[3] != "--": sys.exit("usage: local.py unit <id> <text|vision|path.gguf|-> -- <command ...>")
        sys.exit(unit(a[1], a[2], a[4:]))
    elif op == "stop": stop()
    elif op == "free": print(free_pct())
    elif op == "elapsed": print(int(elapsed()))
    elif op == "note": note(" ".join(a[1:]))
    elif op == "launch":                          # its own session: a closed terminal does not stop it, and the whole run can be signalled as a group
        p = subprocess.Popen(["bash", str(ROOT / "tools/run.sh"), "_run"], cwd=ROOT, stdin=subprocess.DEVNULL,
                             stdout=open(L / "run.log", "a"), stderr=subprocess.STDOUT, start_new_session=True)
        print(p.pid)
    else: print(__doc__); sys.exit(0 if op in ("-h", "--help") else 2)

if __name__ == "__main__":
    main()
