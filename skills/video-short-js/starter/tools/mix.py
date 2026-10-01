# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "scipy", "soundfile", "pyloudnorm"]
# ///
"""Mix the stems in audio/stems/ (score.wav, sfx.wav, vo.wav; any may be missing) into
audio/final_mix.wav, plus final_mix.m4a for the HTML page. Run from the project root.

    uv run tools/mix.py [--score-db 0] [--sfx-db 0] [--vo-db -3] [--duck-db -7]

The bed (score + sfx) dips under each narration line, then the whole mix is set to
-16 LUFS integrated with peaks held under -1.5 dBFS. Prints what a listener would
care about: how far each spoken line sits above the bed underneath it.
"""
import argparse, json, subprocess, sys
from pathlib import Path
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.ndimage import maximum_filter1d, uniform_filter1d

root = Path.cwd()
VIDEO = json.loads((root / "video.json").read_text())
ap = argparse.ArgumentParser()
ap.add_argument("--score-db", type=float, default=0.0)
ap.add_argument("--sfx-db", type=float, default=0.0)
ap.add_argument("--vo-db", type=float, default=-3.0)
ap.add_argument("--duck-db", type=float, default=-7.0)
ap.add_argument("--target", type=float, default=-16.0)
a = ap.parse_args()

SR = 48000; N = int(round(SR * VIDEO["duration"]))
def load(name):
    if not (root / "audio/stems" / name).exists():
        print(f"(no {name}: mixing without it)"); return np.zeros((N, 2))
    x, sr = sf.read(root / "audio/stems" / name, dtype="float64", always_2d=True)
    assert sr == SR, f"{name}: {sr} Hz"
    if x.shape[1] == 1: x = np.repeat(x, 2, axis=1)
    assert abs(len(x) - N) <= 2, f"{name}: {len(x)} samples, expected {N}"
    return np.pad(x, ((0, max(0, N - len(x))), (0, 0)))[:N]
db = lambda d: 10 ** (d / 20)
score, sfx, vo = load("score.wav") * db(a.score_db), load("sfx.wav") * db(a.sfx_db), load("vo.wav") * db(a.vo_db)

# where the voice is: from the narration agent's own measurements
# where the voice is: audio/vo/lines.json, a list of {"start": s, "measured_end": s} written by whoever made the narration
lp = root / "audio/vo/lines.json"
lines = json.loads(lp.read_text()) if lp.exists() else []
lines = lines["lines"] if isinstance(lines, dict) else lines
spans = [(float(l["start"]), float(l.get("measured_end") or l.get("end"))) for l in lines]

# duck envelope: ease down 0.25 s before a line, hold, ease back over 0.6 s
t = np.arange(N) / SR
env = np.zeros(N)
for s, e in spans:
    env = np.maximum(env, np.clip((t - (s - .25)) / .25, 0, 1) * np.clip(((e + .6) - t) / .6, 0, 1))
env = .5 - .5 * np.cos(np.pi * env)
gs = (1 - env * (1 - db(a.duck_db)))[:, None]            # score dips the full amount
gx = (1 - env * (1 - db(a.duck_db * .6)))[:, None]       # effects a little less: the picture still needs them
bed = score * gs + sfx * gx
mix = bed + vo

meter = pyln.Meter(SR)
gain = db(a.target - meter.integrated_loudness(mix))
mix, bed, vo = mix * gain, bed * gain, vo * gain
# safety limiter: hold the needed reduction 10 ms around each peak, smooth over 4 ms (shorter than the hold, so peaks stay covered)
ceil = db(-1.5); need = np.maximum(1, np.abs(mix).max(axis=1) / ceil)
need = uniform_filter1d(maximum_filter1d(need, int(SR * .010)), int(SR * .004))
mix = mix / np.maximum(1, need)[:, None]
fade = np.clip((VIDEO["duration"] - t) / .35, 0, 1)[:, None]; mix *= fade

out = root / "audio/final_mix.wav"
sf.write(out, mix, SR, subtype="PCM_24")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(root / "audio/final_mix.m4a")], check=True)

print(f"integrated {meter.integrated_loudness(mix):.1f} LUFS  peak {20 * np.log10(np.abs(mix).max()):.1f} dBFS  gain applied {20 * np.log10(gain):+.1f} dB")
rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
for i, (s, e) in enumerate(spans):
    i0, i1 = int(s * SR), int(e * SR)
    print(f"line {i + 1} {s:5.2f}-{e:5.2f}s  voice {rms(vo[i0:i1]):6.1f} dB  bed {rms(bed[i0:i1]):6.1f} dB  voice over bed {rms(vo[i0:i1]) - rms(bed[i0:i1]):+5.1f} dB")
step = max(2.0, VIDEO["duration"] / 6)            # loudness by stretch of the film: does the arc go where the story goes?
a0 = 0.0
while a0 < VIDEO["duration"] - .01:
    sl = slice(int(a0 * SR), int(min(VIDEO["duration"], a0 + step) * SR))
    print(f"{a0:5.1f}-{min(VIDEO['duration'], a0 + step):5.1f}s  mix {rms(mix[sl]):6.1f}  score {rms(score[sl] * gain):6.1f}  sfx {rms(sfx[sl] * gain):6.1f} dB rms")
    a0 += step
