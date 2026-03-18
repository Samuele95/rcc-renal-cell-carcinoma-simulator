#!/bin/bash
# Push the RCC Simulator to GitHub.
# - First run: creates the repo and pushes.
# - Subsequent runs: commits tracked changes and pushes.
#
# Only stages files already tracked by git plus new files that pass
# .gitignore rules. Never force-adds ignored content.
#
# Requires: gh (GitHub CLI), authenticated via `gh auth login`.
#
# Usage:
#   chmod +x push_to_github.sh
#   ./push_to_github.sh                  # auto-generated commit message
#   ./push_to_github.sh "my message"     # custom commit message

set -euo pipefail

REPO_NAME="rcc-renal-cell-carcinoma-simulator"
DESCRIPTION="Agent-based model of renal cell carcinoma with glucose sensing, sex-stratified treatment response, and Bayesian optimization"
REMOTE="origin"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"

echo ""
echo "  RCC Simulator — GitHub Push"
echo "  ================================================="
echo ""

# ── 1. Check prerequisites ──────────────────────────────────────
if ! command -v gh >/dev/null 2>&1; then
    echo "Error: GitHub CLI (gh) not found. Install it first."
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "Error: GitHub CLI not authenticated. Run 'gh auth login' first."
    exit 1
fi

# ── 2. Create repo if remote doesn't exist yet ──────────────────
if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
    echo "  [*] No remote '$REMOTE' found — creating GitHub repository..."
    gh repo create "$REPO_NAME" \
        --public \
        --description "$DESCRIPTION" \
        --source . \
        --remote "$REMOTE" \
        --push
    echo ""
    echo "  Done! Repository created and pushed."
    echo "  https://github.com/Samuele95/$REPO_NAME"
    echo ""
    exit 0
fi

# ── 3. Stage changes selectively ─────────────────────────────────
#   - Update all tracked files (modifications + deletions)
#   - Add new untracked files that pass .gitignore (no --force)
echo "  [*] Staging changes..."
git add --update                  # tracked modifications & deletions
git add --ignore-errors . 2>/dev/null || true   # new files respecting .gitignore

# Check if anything was actually staged
if git diff --cached --quiet; then
    echo "  [*] Working tree clean — nothing to commit."
    echo ""

    # Still push in case local commits haven't been pushed yet
    UNPUSHED=$(git log "$REMOTE/$BRANCH..$BRANCH" --oneline 2>/dev/null | wc -l)
    if [ "$UNPUSHED" -gt 0 ]; then
        echo "  [*] Pushing $UNPUSHED unpushed commit(s)..."
        git push "$REMOTE" "$BRANCH"
        echo ""
        echo "  Done! Pushed to: https://github.com/Samuele95/$REPO_NAME"
    else
        echo "  Nothing to push — already up to date."
    fi
    echo ""
    exit 0
fi

# ── 4. Show what will be committed ───────────────────────────────
echo ""
echo "  Files to commit:"
git diff --cached --stat | sed 's/^/    /'
echo ""

# ── 5. Commit ────────────────────────────────────────────────────
if [ $# -ge 1 ]; then
    MSG="$1"
else
    ADDED=$(git diff --cached --diff-filter=A --name-only | wc -l)
    MODIFIED=$(git diff --cached --diff-filter=M --name-only | wc -l)
    DELETED=$(git diff --cached --diff-filter=D --name-only | wc -l)
    PARTS=""
    [ "$ADDED" -gt 0 ]    && PARTS="${PARTS}${ADDED} added, "
    [ "$MODIFIED" -gt 0 ] && PARTS="${PARTS}${MODIFIED} modified, "
    [ "$DELETED" -gt 0 ]  && PARTS="${PARTS}${DELETED} deleted, "
    PARTS="${PARTS%, }"
    MSG="Update: ${PARTS:-minor changes}"
fi

echo "  [*] Committing: $MSG"
git commit -m "$MSG"

# ── 6. Push ──────────────────────────────────────────────────────
echo "  [*] Pushing $BRANCH to $REMOTE..."
git push "$REMOTE" "$BRANCH"

echo ""
echo "  Done! Pushed to: https://github.com/Samuele95/$REPO_NAME"
echo ""
