#!/bin/bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$PROJECT_DIR/automation/logs"
STAMP="$(date +%Y-%m-%d_%H-%M-%S)"
LOG_FILE="$LOG_DIR/run-learning-cycle-$STAMP.log"

mkdir -p "$LOG_DIR"

run_step() {
  local name="$1"
  shift

  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$name" | tee -a "$LOG_FILE"
  "$@" 2>&1 | tee -a "$LOG_FILE"
}

run_step "Import inbox links" bash "$PROJECT_DIR/scripts/import_links.sh"
run_step "Archive Feishu links" bash "$PROJECT_DIR/scripts/archive_feishu_links.sh"
run_step "Generate note drafts" bash "$PROJECT_DIR/scripts/generate_note_drafts.sh"
run_step "Check configured sources" bash "$PROJECT_DIR/scripts/check_sources.sh"
run_step "Update change index" bash "$PROJECT_DIR/scripts/update_change_index.sh"
run_step "Generate weekly digest" bash "$PROJECT_DIR/scripts/generate_weekly_digest.sh"

printf '\nCompleted learning cycle. Log: %s\n' "$LOG_FILE" | tee -a "$LOG_FILE"
