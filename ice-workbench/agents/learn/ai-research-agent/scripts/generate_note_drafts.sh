#!/bin/bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IMPORT_DIR="$PROJECT_DIR/knowledge/raw/inbox-imports"
WEB_DIR="$PROJECT_DIR/knowledge/raw/web-fetches"
OUT_DIR="$PROJECT_DIR/knowledge/notes/drafts"

mkdir -p "$OUT_DIR"

slugify() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed 's#[^a-z0-9._-]#-#g; s#--*#-#g; s#^-##; s#-$##'
}

extract_field() {
  local field="$1"
  local file="$2"
  grep -E "^- ${field}: " "$file" | head -n 1 | sed "s#^- ${field}: ##"
}

write_draft() {
  local source_file="$1"
  local title url source_type source_name draft_name out_file

  title="$(extract_field "Title" "$source_file")"
  url="$(extract_field "URL" "$source_file")"
  source_type="$(extract_field "Type" "$source_file")"

  if [ -z "$title" ]; then
    title="Untitled Draft"
  fi

  draft_name="$(slugify "$title")"
  if [ -z "$draft_name" ]; then
    draft_name="draft-$(basename "$source_file" .md)"
  fi

  out_file="$OUT_DIR/${draft_name}.md"
  if [ -f "$out_file" ]; then
    return
  fi

  {
    echo "# Draft: $title"
    echo
    echo "## Source"
    echo
    echo "- URL: ${url:-unknown}"
    echo "- Type: ${source_type:-unknown}"
    echo "- Generated At: $(date)"
    echo
    echo "## Core Claims"
    echo
    echo "- Pending extraction"
    echo "- Pending evidence review"
    echo
    echo "## Recommended Takeaways"
    echo
    echo "- Pending extraction"
    echo
    echo "## Comparison With Existing Notes"
    echo
    echo "- Reinforces: pending"
    echo "- Updates: pending"
    echo "- Conflicts: pending"
    echo
    echo "## Discussion Needed"
    echo
    echo "- Should this become a stable note or stay as a transient source?"
  } > "$out_file"

  printf 'Drafted %s\n' "$out_file"
}

if [ -d "$IMPORT_DIR" ]; then
  for file in "$IMPORT_DIR"/*.md; do
    [ -e "$file" ] || continue
    write_draft "$file"
  done
fi

if [ -d "$WEB_DIR" ]; then
  for file in "$WEB_DIR"/*.md; do
    [ -e "$file" ] || continue
    write_draft "$file"
  done
fi
