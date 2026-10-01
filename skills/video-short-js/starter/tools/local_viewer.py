#!/usr/bin/env python3
"""A first-time viewer, played by a local vision model: can the film be followed with no words?

    python3 tools/local_viewer.py output/<name>.mp4 [--model path.gguf --mmproj path.gguf]

Runs entirely on this machine through llama.cpp's llama-server, with a vision model that is
ALREADY on disk: nothing is downloaded. Without --model it looks for a GGUF with an mmproj
beside it under $LOCAL_MODELS_DIR, LM Studio's models folder, or ~/models.
The film is shown a few frames at a time, because a small model reads a few pictures well and
a long strip badly; the per-part notes then go back as plain text for one last question:
what was it about? The model is told nothing about the story. Stdlib only.
"""
import argparse, base64, json, os, re, signal, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

BASE_URL = "http://127.0.0.1:8089/v1"          # loopback only: this call never leaves the machine

def find_model():
    roots = [os.environ.get("LOCAL_MODELS_DIR")]
    try: roots.append(json.loads((Path.home() / ".cache/lm-studio/settings.json").read_text()).get("downloadsFolder"))
    except Exception: pass
    roots += [str(Path.home() / ".lmstudio/models"), str(Path.home() / ".cache/lm-studio/models"), str(Path.home() / "models")]
    for r in filter(None, roots):
        for mm in sorted(Path(r).expanduser().rglob("*mmproj*.gguf")) if Path(r).expanduser().is_dir() else []:
            sib = [g for g in mm.parent.glob("*.gguf") if "mmproj" not in g.name.lower()]
            if sib: return sib[0], mm
    return None, None

def free_pct():
    out = subprocess.run(["memory_pressure"], capture_output=True, text=True).stdout
    m = re.search(r"free percentage:\s*(\d+)%", out)
    return int(m.group(1)) if m else None

def ask(content, max_tokens=260):
    body = json.dumps({"model": "local", "temperature": 0.2, "max_tokens": max_tokens, "chat_template_kwargs": {"enable_thinking": False},
                       "messages": [{"role": "user", "content": content}]}).encode()
    t0 = time.time()
    with urllib.request.urlopen(urllib.request.Request(BASE_URL + "/chat/completions", body, {"Content-Type": "application/json"}), timeout=600) as r:
        d = json.load(r)
    text = re.sub(r"<think>.*?</think>", "", d["choices"][0]["message"].get("content") or "", flags=re.S).strip()
    return text, time.time() - t0, d.get("usage", {})

def disk_free_gb():
    try:
        out = subprocess.run(["diskutil", "info", "/System/Volumes/Data"], capture_output=True, text=True).stdout
        return int(re.search(r"Container Free Space:.*\((\d+) Bytes\)", out).group(1)) / 1e9
    except Exception: return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--model"); ap.add_argument("--mmproj"); ap.add_argument("--frames-per-part", type=int, default=4)
    a = ap.parse_args(); video = Path(a.video)
    gguf, mmproj = (Path(a.model), Path(a.mmproj)) if a.model and a.mmproj else find_model()
    if not gguf: sys.exit("no local vision GGUF with an mmproj found; pass --model and --mmproj. This tool never downloads one.")
    assert video.exists(), "video not found"
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)], capture_output=True, text=True).stdout)
    parts = max(2, round(dur / 10)); n = a.frames_per_part
    ACTS = [[round((i + (j + .5) / n) * dur / parts, 1) for j in range(n)] for i in range(parts)]
    # both walls before loading: a model that fits in memory still freezes a machine whose swap has nowhere to grow
    free, disk = free_pct(), disk_free_gb(); print(f"model: {gguf.name}\nmemory free before load: {free}%   disk free: {disk and round(disk, 1)} GB")
    if free is not None and free < int(os.environ.get("MIN_FREE", "60")): sys.exit("not enough free memory to load a vision model safely (want 60%); close something, or lower MIN_FREE knowingly")
    if disk is not None and disk < 3: sys.exit("under 3 GB of disk free: swap cannot grow; free space first")
    tmp = Path(tempfile.mkdtemp(prefix="viewer-"))
    for times in ACTS:
        for t in times:   # 768 px on the long edge: more than that overflows a small model's context for no gain
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(video), "-frames:v", "1", "-vf", "scale=768:-2", "-q:v", "3", str(tmp / f"{t:06.1f}.jpg")], check=True)
    srv = subprocess.Popen(["llama-server", "-m", str(gguf), "--mmproj", str(mmproj), "--host", "127.0.0.1", "--port", "8089", "-c", "12288", "--parallel", "1",
                            "-ngl", "99", "--chat-template-kwargs", '{"enable_thinking":false}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        for _ in range(180):                       # wait on the server's own readiness signal
            try:
                if json.load(urllib.request.urlopen("http://127.0.0.1:8089/health", timeout=2)).get("status") == "ok": break
            except Exception: pass
            if srv.poll() is not None: sys.exit("llama-server exited during load")
            time.sleep(1)
        else: sys.exit("llama-server never became ready")
        print(f"memory free after load: {free_pct()}%")
        notes = []
        for times in ACTS:
            content = [{"type": "text", "text": f"These {len(times)} pictures are consecutive moments, in order, from a short hand-made animated film with no dialogue. In two or three plain sentences, say what is happening across them. Describe only what you can see."}]
            for t in times:
                content.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode((tmp / f"{t:06.1f}.jpg").read_bytes()).decode()}})
            text, dt, usage = ask(content)
            flag = "  [suspiciously fast: treat as a failed read]" if dt < 1.5 else ""
            print(f"\n[{times[0]:.0f}-{times[-1]:.0f}s] {dt:.1f}s, {usage.get('prompt_tokens', '?')} prompt tokens{flag}\n{text}")
            notes.append(f"Part {len(notes) + 1}: {text}")
        text, dt, _ = ask([{"type": "text", "text": "A viewer wrote these notes while watching a short animated film with no dialogue, part by part:\n\n" + "\n".join(notes) +
                            "\n\nAnswer three questions, one short sentence each. 1. What is the film about? 2. What do the characters do about their problem? 3. What feeling does the ending leave?"}], 220)
        print(f"\n[whole film] {dt:.1f}s\n{text}")
    finally:
        os.killpg(srv.pid, signal.SIGTERM)          # whoever loads owns the unload
        try: srv.wait(timeout=20)
        except Exception: os.killpg(srv.pid, signal.SIGKILL)
        time.sleep(2); print(f"\nmemory free after unload: {free_pct()}%")

if __name__ == "__main__":
    main()
