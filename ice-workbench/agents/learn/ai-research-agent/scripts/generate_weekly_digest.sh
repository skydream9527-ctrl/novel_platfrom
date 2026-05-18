#!/bin/bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RAW_DIR="$PROJECT_DIR/knowledge/raw/source-checks"
OUT_DIR="$PROJECT_DIR/knowledge/news-digest"
STAMP="$(date +%Y-%m-%d)"
OUT_FILE="$OUT_DIR/$STAMP-weekly.md"

mkdir -p "$OUT_DIR"

LATEST_FILE="$(ls -1 "$RAW_DIR"/*.md 2>/dev/null | sort | tail -n 1 || true)"

{
  echo "# Weekly AI Digest $STAMP"
  echo
  echo "## Summary"
  echo
  if [ -n "$LATEST_FILE" ]; then
    echo "- Latest source snapshot: \



  \

`$(basename "$LATEST_FILE")`"
  else
    echo "- No source snapshot found yet. Run \



  \

`bash scripts/check_sources.sh` first."
  fi
  echo "- Fill this report with notable changes, new tools, deprecations, and best-option updates."
  echo
  echo "## Important Changes"
  echo
  echo "- Pending review"
  echo
  echo "## Candidate Best Options"
  echo
  echo "- Pending review"
  echo
  echo "## Discussion Needed"
  echo
  echo "- Pending review"
} > "$OUT_FILE"

printf 'Wrote %s\n' "$OUT_FILE"
