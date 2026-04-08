#!/usr/bin/env bash
set -euo pipefail

# pick-variant.sh — merge the winning design variant into base and clean up the rest
#
# Usage: pick-variant.sh <tool-name> [--base <branch>]
#   e.g. pick-variant.sh bmad
#        pick-variant.sh stitch --base develop

WINNER=""
BASE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --base) BASE="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: pick-variant.sh <tool-name> [--base <branch>]"
            echo ""
            echo "Merges design-variant-<tool> into the base branch and cleans up"
            echo "all other design-variant-* worktrees and branches."
            echo ""
            echo "Options:"
            echo "  --base BRANCH  Target branch to merge into (default: main)"
            exit 0
            ;;
        *) WINNER="$1"; shift ;;
    esac
done

if [[ -z "$WINNER" ]]; then
    echo "Error: specify which tool won. Usage: pick-variant.sh <tool-name>" >&2
    exit 1
fi

WINNING_BRANCH="design-variant-${WINNER}"

# Default base branch
if [[ -z "$BASE" ]]; then
    BASE=$(git rev-parse --verify main &>/dev/null && echo "main" || echo "master")
fi

# Verify the winning branch exists
if ! git rev-parse --verify "$WINNING_BRANCH" &>/dev/null; then
    echo "Error: branch '$WINNING_BRANCH' does not exist." >&2
    echo "Available design-variant branches:"
    git branch --list 'design-variant-*' | sed 's/^/  /'
    exit 1
fi

# Verify base branch exists
if ! git rev-parse --verify "$BASE" &>/dev/null; then
    echo "Error: base branch '$BASE' does not exist." >&2
    exit 1
fi

# Check the winning branch has commits beyond the fork point
COMMIT_COUNT=$(git log "$BASE".."$WINNING_BRANCH" --oneline | wc -l | tr -d ' ')
if [[ "$COMMIT_COUNT" -eq 0 ]]; then
    echo "Warning: '$WINNING_BRANCH' has no new commits beyond '$BASE'." >&2
    read -rp "Continue anyway? [y/N]: " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy] ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

# Collect all variant branches
ALL_VARIANTS=()
while IFS= read -r branch; do
    branch=$(echo "$branch" | sed 's/^[* ]*//')
    ALL_VARIANTS+=("$branch")
done < <(git branch --list 'design-variant-*')

OTHER_VARIANTS=()
for b in "${ALL_VARIANTS[@]}"; do
    if [[ "$b" != "$WINNING_BRANCH" ]]; then
        OTHER_VARIANTS+=("$b")
    fi
done

# Show plan and confirm
echo ""
echo "=== Pick Variant: $WINNER ==="
echo ""
echo "  Merge:  $WINNING_BRANCH -> $BASE ($COMMIT_COUNT commits)"
if [[ ${#OTHER_VARIANTS[@]} -gt 0 ]]; then
    echo "  Remove: ${OTHER_VARIANTS[*]}"
else
    echo "  Remove: (no other variants)"
fi
echo ""
read -rp "Proceed with merge? [y/N]: " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy] ]]; then
    echo "Cancelled."
    exit 0
fi

# Step 1: Switch to base branch
echo ""
echo "-- Checking out $BASE --"
git checkout "$BASE"

# Step 2: Remove the winning branch's worktree first (if it exists), before merging
WINNING_WORKTREE=$(git worktree list --porcelain | grep -B2 "branch refs/heads/$WINNING_BRANCH" | grep '^worktree ' | sed 's/^worktree //' || true)
if [[ -n "$WINNING_WORKTREE" ]]; then
    echo "-- Removing winning branch worktree: $WINNING_WORKTREE --"
    git worktree remove "$WINNING_WORKTREE"
fi

# Step 3: Merge the winner
echo "-- Merging $WINNING_BRANCH into $BASE --"
git merge "$WINNING_BRANCH" --no-ff -m "Merge design variant '$WINNER' into $BASE"

# Step 4: Remove other variant worktrees and branches
for branch in "${OTHER_VARIANTS[@]}"; do
    # Remove worktree if it exists
    WORKTREE_PATH=$(git worktree list --porcelain | grep -B2 "branch refs/heads/$branch" | grep '^worktree ' | sed 's/^worktree //' || true)
    if [[ -n "$WORKTREE_PATH" ]]; then
        echo "-- Removing worktree: $WORKTREE_PATH --"
        git worktree remove "$WORKTREE_PATH"
    fi
    # Delete the branch
    echo "-- Deleting branch: $branch --"
    git branch -D "$branch"
done

# Step 5: Delete the winning branch (already merged)
echo "-- Deleting merged branch: $WINNING_BRANCH --"
git branch -d "$WINNING_BRANCH"

# Summary
echo ""
echo "=== Done ==="
echo "  Merged:  $WINNING_BRANCH -> $BASE"
echo "  Deleted: ${ALL_VARIANTS[*]}"
REMAINING_WORKTREES=$(git worktree list --porcelain | grep -c '^worktree ' || true)
echo "  Worktrees remaining: $REMAINING_WORKTREES"
echo ""

# Offer to push
read -rp "Push to remote? [y/N]: " PUSH
if [[ "$PUSH" =~ ^[Yy] ]]; then
    git push origin "$BASE"
    echo "Pushed $BASE to origin."
else
    echo "Not pushed. Run 'git push origin $BASE' when ready."
fi
