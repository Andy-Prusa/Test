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
echo "  pre-commit  checks the page is rebuilt, then runs test_parity.py and"
echo "              test_validation.py, and blocks the commit if any fails."
echo
echo "Skip for one commit with:  git commit --no-verify"

# Say now what is missing, rather than at the first blocked commit.
missing=$(python3 - <<'PY' 2>/dev/null || true
import importlib.util
print(" ".join(m for m in ("numpy", "scipy", "matplotlib")
                if importlib.util.find_spec(m) is None))
PY
)
if [ -n "${missing:-}" ]; then
    echo
    echo "WARNING: these are needed and not installed: $missing"
    echo "         pip install -r requirements.txt"
fi
if ! command -v node >/dev/null 2>&1; then
    echo
    echo "WARNING: node is not installed, so model.js cannot be run and the"
    echo "         parity test cannot check the port against the Python."
fi
