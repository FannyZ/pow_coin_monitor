#!/usr/bin/env bash
# Create GitHub repo FannyZ/pow_coin_monitor and push (requires: gh auth login OR pre-created empty repo)
set -euo pipefail
cd "$(dirname "$0")/.."

REPO="${GITHUB_REPO:-FannyZ/pow_coin_monitor}"
VISIBILITY="${GITHUB_VISIBILITY:-public}"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git repository. Run from pow_coin_monitor root."
  exit 1
fi

if gh auth status >/dev/null 2>&1; then
  echo "Creating repo ${REPO} via GitHub CLI..."
  gh repo create "${REPO}" \
    --"${VISIBILITY}" \
    --source=. \
    --remote=origin \
    --push \
    --description "Daily scanner for new GPU/PoW mineable coins with Telegram alerts"
  echo "Done: https://github.com/${REPO}"
  exit 0
fi

echo "gh not logged in. Using SSH push to existing remote repo..."
REMOTE="git@github.com:${REPO}.git"
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "${REMOTE}"
else
  git remote add origin "${REMOTE}"
fi

echo "Pushing to ${REMOTE} ..."
echo "If repo does not exist yet, create it first:"
echo "  https://github.com/new  → name: pow_coin_monitor, no README"
git push -u origin main

echo "Done: https://github.com/${REPO}"
