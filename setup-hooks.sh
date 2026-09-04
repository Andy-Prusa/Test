#!/bin/sh
#
# setup-hooks.sh — point git at the hooks committed in .githooks/.
#
# Git does not clone hooks, and .git/hooks is not version controlled, so every
# fresh clone starts with no gate on it. Run this once after cloning:
#
#     ./setup-hooks.sh
#
# It sets core.hooksPath, which is per-clone local config. Undo with:
#
#     git config --unset core.hooksPath

set -eu

root=$(git rev-parse --show-toplevel)
cd "$root"

chmod +x .githooks/* 2>/dev/null || true
git config core.hooksPath .githooks

echo "hooks enabled: core.hooksPath -> .githooks"
echo
echo "  pre-commit  runs test_parity.py then test_validation.py and blocks"
echo "              the commit if either fails."
echo
echo "Skip for one commit with:  git commit --no-verify"
