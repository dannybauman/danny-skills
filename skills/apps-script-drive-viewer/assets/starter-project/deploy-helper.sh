#!/usr/bin/env bash
# deploy-helper.sh
#
# Wraps the common clasp + Apps Script deploy commands.
# Run from this project directory (where .clasp.json lives).
#
# Usage:
#   ./deploy-helper.sh push                     — push local changes to Apps Script
#   ./deploy-helper.sh deploy "description"     — create a NEW deployment (new URL)
#   ./deploy-helper.sh redeploy "description"   — update EXISTING deployment (URL stays stable)
#   ./deploy-helper.sh url                      — print the current web app URL
#   ./deploy-helper.sh logs                     — show recent execution logs

set -euo pipefail

if ! command -v clasp >/dev/null 2>&1; then
  echo "clasp not installed. Run: npm install -g @google/clasp"
  exit 1
fi

if [ ! -f .clasp.json ]; then
  echo ".clasp.json not found in current directory. Run from your project folder."
  exit 1
fi

cmd="${1:-help}"

case "$cmd" in
  push)
    clasp push
    ;;
  deploy)
    desc="${2:-New deploy $(date +%Y-%m-%d_%H:%M)}"
    clasp deploy --description "$desc"
    echo ""
    echo "⚠️  New deployment created — URL is different from any previous deployment."
    echo "    To keep a stable URL across code changes, use 'redeploy' instead."
    ;;
  redeploy)
    desc="${2:-Updated $(date +%Y-%m-%d_%H:%M)}"
    DEPLOY_ID=$(clasp deployments | grep -v '@HEAD' | tail -1 | awk '{print $2}')
    if [ -z "$DEPLOY_ID" ]; then
      echo "No existing deployment found. Use 'deploy' to create one first."
      exit 1
    fi
    echo "Redeploying existing deployment: $DEPLOY_ID"
    clasp redeploy "$DEPLOY_ID" --description "$desc"
    ;;
  url)
    DEPLOY_ID=$(clasp deployments | grep -v '@HEAD' | tail -1 | awk '{print $2}')
    if [ -z "$DEPLOY_ID" ]; then
      echo "No deployment yet. Run 'deploy' first."
      exit 1
    fi
    echo "https://script.google.com/macros/s/${DEPLOY_ID}/exec"
    ;;
  logs)
    clasp logs
    ;;
  help|*)
    cat <<EOF
deploy-helper.sh — Apps Script deploy wrapper

Commands:
  push                    — push local changes to Apps Script project
  deploy "description"    — create a NEW deployment (new URL, recipients re-bookmark)
  redeploy "description"  — update EXISTING deployment (URL stays stable, preferred)
  url                     — print the current deployed web app URL
  logs                    — recent execution logs from Apps Script

Typical workflow:
  ./deploy-helper.sh push                          # after editing locally
  ./deploy-helper.sh redeploy "Added tier filter"  # promote to production
  ./deploy-helper.sh url                           # confirm URL

First-time setup happens in the Apps Script editor (configure access settings),
not via this script. See README.md.
EOF
    ;;
esac
