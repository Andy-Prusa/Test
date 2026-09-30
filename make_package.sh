#!/usr/bin/env bash
# Build the shareable package: a self-contained snapshot of the tracked tree
# at the current commit, plus a provenance stamp.
#
# Everything it contains carries the copyright notice, because the notice
# lives in the source files rather than being added at packaging time. If you
# add a source file, stamp it there too.
#
#     ./make_package.sh [outdir]      default: ./dist
set -euo pipefail
cd "$(dirname "$0")"

command -v zip >/dev/null || { echo "need zip" >&2; exit 1; }
git diff --quiet || echo "WARNING: uncommitted changes are NOT in the package" >&2

SHA=$(git rev-parse --short HEAD)
OUT=${1:-dist}
NAME="apnoea-model-$SHA"
STAGE="$OUT/$NAME"

rm -rf "$STAGE" "$OUT/$NAME.zip"
mkdir -p "$STAGE"
git archive HEAD | tar -x -C "$STAGE"

printf 'commit   %s\ndate     %s\npacked   %s\n' \
  "$(git rev-parse HEAD)" \
  "$(git log -1 --format=%cd --date=short)" \
  "$(date -u +%Y-%m-%dT%H:%MZ)" > "$STAGE/PROVENANCE.txt"

# The hook artefacts are noise to a recipient who is not committing.
rm -rf "$STAGE/.githooks" "$STAGE/setup-hooks.sh" "$STAGE/.gitignore"

for f in LICENSE CITATION.cff README.md airway_scenario.html apnoea_core.py; do
  [ -f "$STAGE/$f" ] || { echo "missing from package: $f" >&2; exit 1; }
done

( cd "$OUT" && zip -qr "$NAME.zip" "$NAME" )
echo "built $OUT/$NAME.zip"
