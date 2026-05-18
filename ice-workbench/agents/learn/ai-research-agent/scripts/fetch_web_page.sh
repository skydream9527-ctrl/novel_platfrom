#!/bin/bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$PROJECT_DIR/knowledge/raw/web-fetches"

mkdir -p "$OUT_DIR"

if [ "$#" -lt 1 ]; then
  printf 'Usage: %s <url>\n' "$0" >&2
  exit 1
fi

URL="$1"
STAMP="$(date +%Y-%m-%d_%H-%M-%S)"
SLUG="$(printf '%s' "$URL" | sed 's#https\?://##; s#[^A-Za-z0-9._-]#_#g')"
OUT_FILE="$OUT_DIR/${STAMP}_${SLUG}.md"

HTML="$(curl -L --max-time 30 --silent --show-error "$URL")"
TITLE="$(printf '%s' "$HTML" | perl -0ne 'if (/<title[^>]*>(.*?)<\/title>/is) { $t=$1; $t =~ s/\s+/ /g; $t =~ s/^\s+|\s+$//g; print $t; }')"
TEXT="$(printf '%s' "$HTML" | perl -0pe 's/<script\b[^>]*>.*?<\/script>//gis; s/<style\b[^>]*>.*?<\/style>//gis; s/<[^>]+>/\n/g; s/&nbsp;/ /g; s/&amp;/\&/g; s/\r//g;' | awk 'length($0) > 0' | sed 's/^\s\+//; s/\s\+$//' | awk '!seen[$0]++' | perl -0pe 's/\n{3,}/\n\n/g')"

{
  echo "# Web Fetch"
  echo
  echo "- URL: $URL"
  echo "- Title: ${TITLE:-Untitled}"
  echo "- Fetched At: $(date)"
  echo
  echo "## Extracted Text"
  echo
  printf '%s\n' "$TEXT"
} > "$OUT_FILE"

printf 'Wrote %s\n' "$OUT_FILE"
