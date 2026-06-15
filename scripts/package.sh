#!/usr/bin/env bash
# Build the distributable .skill (a zip of this skill folder).
#
# The archive's top-level folder is the skill's identity (its `name`), not the
# repo directory name — so we stage into a `ograf-graphics/` dir before zipping.
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_NAME="ograf-graphics"
PARENT="$(dirname "$SKILL_DIR")"
OUT="${1:-$PARENT/$SKILL_NAME.skill}"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

# Copy the skill in, excluding everything that must not ship.
rsync -a \
  --exclude='.git/' \
  --exclude='.agents/' \
  --exclude='.DS_Store' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='node_modules/' \
  --exclude='*.skill' \
  "$SKILL_DIR/" "$STAGE/$SKILL_NAME/"

rm -f "$OUT"
( cd "$STAGE" && zip -r -X "$OUT" "$SKILL_NAME" >/dev/null )
echo "Packaged -> $OUT"
