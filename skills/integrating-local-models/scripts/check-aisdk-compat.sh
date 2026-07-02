#!/usr/bin/env bash
# @ai-sdk provider-spec compatibility checker.
#
# The trap: in one app, every @ai-sdk/* provider must share the same
# @ai-sdk/provider MAJOR or they won't interoperate under `ai`. The package's
# own major is NOT a reliable signal — a provider's "v3" can depend on
# @ai-sdk/provider v4 (a different spec) while another provider's "v2" depends
# on v3. Blind `^latest` silently pulls a mismatched spec and breaks at runtime.
#
# This script reports the @ai-sdk/provider major a candidate package@version
# depends on, and compares it to the major already installed in your project.
#
# Usage (run from your project root, where node_modules + lockfile live):
#   check-aisdk-compat.sh @ai-sdk/openai-compatible            # checks the 'latest' dist-tag
#   check-aisdk-compat.sh @ai-sdk/openai-compatible@2.0.50     # checks a specific version
#
# Exit: 0 match, 1 mismatch, 2 usage/lookup error.
set -uo pipefail

TARGET="${1:-}"
[ -z "$TARGET" ] && { sed -n '2,18p' "$0"; exit 2; }

PY="$(command -v python3 || command -v python || true)"
[ -z "$PY" ] && { echo "python3 required" >&2; exit 2; }

# Pick the registry client the PROJECT uses — detect from the lockfile in cwd,
# not whatever happens to be first on PATH. Fall back to PATH order only when
# no lockfile identifies the project.
if [ -f pnpm-lock.yaml ] && command -v pnpm >/dev/null 2>&1; then PM="pnpm"
elif [ -f package-lock.json ] && command -v npm >/dev/null 2>&1; then PM="npm"
elif command -v pnpm >/dev/null 2>&1; then PM="pnpm"
elif command -v npm >/dev/null 2>&1; then PM="npm"
else echo "need pnpm or npm on PATH" >&2; exit 2; fi

major() { printf '%s' "$1" | sed -E 's/[^0-9.]//g' | cut -d. -f1; }

# Reference: @ai-sdk/provider version(s) installed in this project. Handles both
# a hoisted/npm layout (node_modules/@ai-sdk/provider) and pnpm's non-flat store
# (node_modules/.pnpm/@ai-sdk+provider@<version>[_peerhash]) where transitive
# deps are NOT symlinked at the top level.
REF_VERS=""
if [ -f node_modules/@ai-sdk/provider/package.json ]; then
  REF_VERS="$("$PY" -c 'import json;print(json.load(open("node_modules/@ai-sdk/provider/package.json"))["version"])' 2>/dev/null)"
else
  REF_VERS="$(ls -d node_modules/.pnpm/@ai-sdk+provider@* 2>/dev/null | sed -E 's#.*@ai-sdk\+provider@##; s#_.*$##' | sort -u | tr '\n' ' ')"
fi
REF_MAJORS="$(for v in $REF_VERS; do [ -n "$v" ] && major "$v"; done | sort -u | tr '\n' ' ' | sed 's/ *$//')"
if [ -z "$REF_MAJORS" ]; then
  echo "⚠ no installed @ai-sdk/provider found (checked node_modules/ and node_modules/.pnpm/) — run from your project root after installing your other @ai-sdk providers."
  echo "  (continuing: will only report what the candidate depends on)"
fi

# Candidate: resolve its @ai-sdk/provider dependency.
DEPS_JSON="$($PM view "$TARGET" dependencies --json 2>/dev/null)"
[ -z "$DEPS_JSON" ] && { echo "✗ could not look up '$TARGET' via $PM view" >&2; exit 2; }
CAND_PROVIDER="$(printf '%s' "$DEPS_JSON" | "$PY" -c 'import json,sys; d=json.load(sys.stdin); print(d.get("@ai-sdk/provider",""))' 2>/dev/null)"
[ -z "$CAND_PROVIDER" ] && { echo "note: '$TARGET' declares no @ai-sdk/provider dep (maybe not an @ai-sdk provider package)"; exit 0; }

CAND_MAJOR="$(major "$CAND_PROVIDER")"
echo "candidate:  $TARGET  →  @ai-sdk/provider $CAND_PROVIDER  (major $CAND_MAJOR)"
if [ -n "$REF_MAJORS" ]; then
  echo "installed:  @ai-sdk/provider $REF_VERS (major(s): $REF_MAJORS)"
  case " $REF_MAJORS " in
    *" $CAND_MAJOR "*)
      echo "✓ MATCH — candidate shares the installed @ai-sdk/provider major; safe to install."
      exit 0 ;;
    *)
      echo "✗ MISMATCH — candidate wants provider major $CAND_MAJOR, project has $REF_MAJORS; these will NOT interoperate."
      echo "  Fix: pick the candidate version line that depends on provider major $REF_MAJORS."
      echo "  Dist-tags often track lines (an 'ai-vN' tag commonly maps to a provider major):  $PM view ${TARGET%@*} dist-tags"
      exit 1 ;;
  esac
fi
exit 0
