#!/bin/bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$PROJECT_DIR/knowledge/raw/source-checks"
STAMP="$(date +%Y-%m-%d_%H-%M-%S)"
OUT_FILE="$OUT_DIR/$STAMP.md"

mkdir -p "$OUT_DIR"

extract_title() {
  local url="$1"
  local html title

  html="$(curl -L --max-time 20 --silent --show-error "$url" 2>/dev/null || true)"
  title="$(printf '%s' "$html" | perl -0ne 'if (/<title[^>]*>(.*?)<\/title>/is) { $t=$1; $t =~ s/\s+/ /g; $t =~ s/^\s+|\s+$//g; print $t; }')"

  if [ -n "$title" ]; then
    printf '%s' "$title"
  else
    printf 'Untitled or blocked'
  fi
}

{
  echo "# Source Check $STAMP"
  echo
  echo "Generated at: $(date)"
  echo
  echo "## Sources"
  echo
  awk '
    /^    - name:/ { name=$0; sub(/^    - name: /, "", name) }
    /^      url:/ { url=$0; sub(/^      url: /, "", url); print name "|" url }
  ' "$PROJECT_DIR/config/sources.yaml" | while IFS='|' read -r name url; do
    title="$(extract_title "$url")"
    echo "- $name"
    echo "  - URL: $url"
    echo "  - Title: $title"
  done
  echo
  echo "## Notes"
  echo
  echo "- This snapshot includes basic web fetch results for configured sources."
  echo "- Use it as an intake queue for manual review, extraction, and discussion."
} > "$OUT_FILE"

printf 'Wrote %s\n' "$OUT_FILE"
