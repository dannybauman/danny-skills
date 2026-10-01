#!/usr/bin/env bash
# Is this machine fit for a render or a local model load right now? Prints the facts; exits 1 when it is not.
# A long build fills disks and swap quietly (package caches, sample libraries, draft renders); check before every heavy step.
set -euo pipefail
min_disk_gb="${MIN_DISK_GB:-3}"; min_free_pct="${MIN_FREE_PCT:-25}"; ok=0
if command -v diskutil >/dev/null 2>&1; then     # macOS: `df` counts purgeable space as free; the container figure is the honest one
  free_bytes=$(diskutil info /System/Volumes/Data 2>/dev/null | sed -n 's/.*Container Free Space:.*(\([0-9]*\) Bytes).*/\1/p')
else
  free_bytes=$(( $(df -Pk . | awk 'NR==2 {print $4}') * 1024 ))
fi
free_gb=$(awk -v b="${free_bytes:-0}" 'BEGIN { printf "%.1f", b / 1e9 }')
echo "disk free:    ${free_gb} GB (want >= ${min_disk_gb})"
awk -v f="$free_gb" -v m="$min_disk_gb" 'BEGIN { exit !(f < m) }' && { echo "  -> too little disk: delete draft renders, prune sample libraries, check package caches"; ok=1; }
if command -v memory_pressure >/dev/null 2>&1; then
  pct=$(memory_pressure | sed -n 's/.*free percentage: \([0-9]*\)%.*/\1/p')
  echo "memory free:  ${pct}% (want >= ${min_free_pct}; a local 9B model wants about 60)"
  [ "${pct:-0}" -lt "$min_free_pct" ] && { echo "  -> too little memory: close apps, unload models, use fewer render workers"; ok=1; }
  echo "swap:         $(sysctl -n vm.swapusage 2>/dev/null | cut -c1-58)"
elif [ -r /proc/meminfo ]; then
  awk '/MemAvailable/ {a=$2} /MemTotal/ {t=$2} END { printf "memory free:  %d%%\n", a * 100 / t }' /proc/meminfo
fi
cores=$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)
echo "suggested render workers: $(( cores > 6 ? 3 : 2 )) (node tools/render.mjs --workers N)"
exit $ok
