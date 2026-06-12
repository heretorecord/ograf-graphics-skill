#!/usr/bin/env bash
# Build the distributable .skill (a zip of this skill folder).
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
NAME="$(basename "$SKILL_DIR")"
PARENT="$(dirname "$SKILL_DIR")"
OUT="${1:-$PARENT/$NAME.skill}"

cd "$PARENT"
rm -f "$OUT"
zip -r -X "$OUT" "$NAME" \
  -x "$NAME/.git/*" \
     "$NAME/**/__pycache__/*" \
     "$NAME/*.skill" \
     "$NAME/**/node_modules/*" \
     "$NAME/**/.DS_Store" >/dev/null
echo "Packaged -> $OUT"
