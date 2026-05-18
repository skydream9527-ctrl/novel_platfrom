#!/bin/bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INDEX_DIR="$PROJECT_DIR/knowledge/raw/change-index"
INDEX_FILE="$INDEX_DIR/index.tsv"
TMP_FILE="$INDEX_DIR/index.tmp.tsv"

mkdir -p "$INDEX_DIR"

if [ ! -f "$INDEX_FILE" ]; then
  printf 'path\tsha1\tupdated_at\n' > "$INDEX_FILE"
fi

printf 'path\tsha1\tupdated_at\n' > "$TMP_FILE"

while IFS= read -r file; do
  checksum="$(shasum "$file" | awk '{print $1}')"
  rel_path="${file#"$PROJECT_DIR"/}"
  printf '%s\t%s\t%s\n' "$rel_path" "$checksum" "$(date '+%Y-%m-%d %H:%M:%S')" >> "$TMP_FILE"
done < <(find "$PROJECT_DIR/knowledge/notes" "$PROJECT_DIR/knowledge/raw" -type f \( -name '*.md' -o -name '*.tsv' \) | sort)

mv "$TMP_FILE" "$INDEX_FILE"
printf 'Wrote %s\n' "$INDEX_FILE"
