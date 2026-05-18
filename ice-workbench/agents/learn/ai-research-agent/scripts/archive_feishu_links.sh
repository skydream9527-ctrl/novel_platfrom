#!/bin/bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INBOX_FILE="$PROJECT_DIR/inbox/links.md"
OUT_DIR="$PROJECT_DIR/knowledge/raw/feishu-imports"

mkdir -p "$OUT_DIR"

if [ ! -f "$INBOX_FILE" ]; then
  printf 'Inbox file not found: %s\n' "$INBOX_FILE" >&2
  exit 1
fi

grep -E '^- \[.\] [0-9]{4}-[0-9]{2}-[0-9]{2} https?://mi\.feishu\.cn/(docx|wiki)/' "$INBOX_FILE" | while IFS= read -r line; do
  source_date="$(printf '%s' "$line" | awk '{print $3}')"
  url="$(printf '%s' "$line" | awk '{print $4}')"
  slug="$(printf '%s' "$url" | sed 's#https\?://##; s#[^A-Za-z0-9._-]#_#g')"
  out_file="$OUT_DIR/${source_date}_${slug}.md"

  if [ -f "$out_file" ]; then
    continue
  fi

  {
    echo "# Feishu Archive Stub"
    echo
    echo "- Archived At: $(date)"
    echo "- Source Date: $source_date"
    echo "- URL: $url"
    echo "- Status: archived-stub"
    echo
    echo "## Capture Notes"
    echo
    echo "- Fetch content through the Feishu skill during an interactive learning run."
    echo "- Save the extracted summary, title, and key claims below."
    echo
    echo "## Summary"
    echo
    echo "- Pending extraction"
    echo
    echo "## Key Claims"
    echo
    echo "- Pending extraction"
  } > "$out_file"

  printf 'Archived %s\n' "$out_file"
done
