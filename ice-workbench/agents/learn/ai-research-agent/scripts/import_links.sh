#!/bin/bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INBOX_FILE="$PROJECT_DIR/inbox/links.md"
OUT_DIR="$PROJECT_DIR/knowledge/raw/inbox-imports"

mkdir -p "$OUT_DIR"

if [ ! -f "$INBOX_FILE" ]; then
  printf 'Inbox file not found: %s\n' "$INBOX_FILE" >&2
  exit 1
fi

extract_title() {
  local url="$1"
  local html title

  html="$(curl -L --max-time 20 --silent --show-error "$url" 2>/dev/null || true)"
  title="$(printf '%s' "$html" | perl -0ne 'if (/<title[^>]*>(.*?)<\/title>/is) { $t=$1; $t =~ s/\s+/ /g; $t =~ s/^\s+|\s+$//g; print $t; }')"

  if [ -n "$title" ]; then
    printf '%s' "$title"
  else
    printf 'Untitled'
  fi
}

extract_type() {
  local url="$1"

  case "$url" in
    *mi.feishu.cn/docx/*) printf 'feishu-docx' ;;
    *mi.feishu.cn/wiki/*) printf 'feishu-wiki' ;;
    *) printf 'web' ;;
  esac
}

grep -E '^- \[.\] [0-9]{4}-[0-9]{2}-[0-9]{2} https?://' "$INBOX_FILE" | while IFS= read -r line; do
  date_part="$(printf '%s' "$line" | awk '{print $3}')"
  url="$(printf '%s' "$line" | awk '{print $4}')"
  item_type="$(extract_type "$url")"
  slug="$(printf '%s' "$url" | sed 's#https\?://##; s#[^A-Za-z0-9._-]#_#g')"
  out_file="$OUT_DIR/${date_part}_${slug}.md"

  if [ -f "$out_file" ]; then
    continue
  fi

  title="$(extract_title "$url")"

  {
    echo "# Inbox Import"
    echo
    echo "- Imported At: $(date)"
    echo "- Source Date: $date_part"
    echo "- URL: $url"
    echo "- Type: $item_type"
    echo "- Title: $title"
    echo
    echo "## Extraction Checklist"
    echo
    echo "- [ ] Read source"
    echo "- [ ] Extract core claims"
    echo "- [ ] Compare against existing notes"
    echo "- [ ] Update best option if needed"
    echo
    echo "## Notes"
    echo
    echo "- Pending extraction"
    echo "- Pending comparison with existing notes"
  } > "$out_file"

  printf 'Imported %s\n' "$out_file"
done
