#!/usr/bin/env bash
# Prove the kit works on this machine: scaffold, build, render two seconds, count the frames.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
tmp="$(mktemp -d)"; trap 'rm -rf "${tmp:?}"' EXIT
bash "$here/new-project.sh" "$tmp/selftest-short" >/dev/null
cd "$tmp/selftest-short"
node tools/build.mjs >/dev/null
node tools/render.mjs --from 0 --to 2 --workers 1 --no-audio --out out.mp4 >/dev/null
frames=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 out.mp4)
[ "$frames" = "48" ] && echo "PASS: 48 frames rendered from the starter scene" || { echo "FAIL: expected 48 frames, got $frames"; exit 1; }
