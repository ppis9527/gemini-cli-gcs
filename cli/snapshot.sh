#!/bin/bash
# Snapshot Generator (Human-Readable Format)
# This script creates a structured Markdown snapshot for Obsidian.
# Usage: /snapshot "Summary content here..."

TIMESTAMP=$(date +"%Y-%m-%d")
HM=$(date +"%H%M")
TITLE="Memory Snapshot - $TIMESTAMP $HM"

# GCS Workspace Integration
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
DEFAULT_OBSIDIAN_DIR="$HOME/gdrive/01_Obsidian/09_memory-snapshot"

# Fallback to project-local snapshots if gdrive not found
if [ -d "$DEFAULT_OBSIDIAN_DIR" ]; then
    OUTPUT_DIR="$DEFAULT_OBSIDIAN_DIR"
else
    OUTPUT_DIR="$PROJECT_ROOT/.gemini/snapshots"
fi

FILE_PATH="$OUTPUT_DIR/${TIMESTAMP}_${HM}_Memory_Summary.md"

SUMMARY_CONTENT=$1
if [ -z "$SUMMARY_CONTENT" ]; then
    SUMMARY_CONTENT="(No summary provided. Please run /snapshot with content or edit this file.)"
fi

mkdir -p "$OUTPUT_DIR"

cat << EOO > "$FILE_PATH"
---
title: $TITLE
date: $TIMESTAMP
tags:
  - memory-snapshot
  - manual-snapshot
  - $TIMESTAMP
  - "#project-09-memory-snapshot"
  - "#module-09-memory-snapshot"
---

# $TITLE

#memory-snapshot #manual-snapshot #$TIMESTAMP

## Summary
$SUMMARY_CONTENT

## Implemented Scope
- (To be filled by agent)

## Implementation Details
- (To be filled by agent)

## Review Outcome (Gemini 2.0 Thinking)
- (To be filled by agent)

## Verification
- (To be filled by agent)

## Git & Storage Outcome
- **代碼位置**: $PROJECT_ROOT
- **存檔路徑**: $FILE_PATH

---
*本快照由 GCS Guardian v1.24.0 手動生成，記錄技術演進。*
EOO

echo "Snapshot generated at: $FILE_PATH"
