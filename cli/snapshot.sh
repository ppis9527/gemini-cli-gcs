#!/bin/bash
# Snapshot Generator (Human-Readable Format)
# This script creates a structured Markdown snapshot for Obsidian.
# Usage: /snapshot "Summary content here..."

TIMESTAMP=$(date +"%Y-%m-%d")
TITLE="Memory Snapshot - $TIMESTAMP"
OUTPUT_DIR="/Users/yjliu/Library/CloudStorage/GoogleDrive-jerryyrliu@gmail.com/我的雲端硬碟/OpenClaw Agents/01_Obsidian/09_memory-snapshot"
FILE_PATH="$OUTPUT_DIR/${TIMESTAMP}_Memory_Summary.md"

SUMMARY_CONTENT=$1
if [ -z "$SUMMARY_CONTENT" ]; then
    SUMMARY_CONTENT="(No summary provided. Please run /snapshot with content or edit this file.)"
fi

mkdir -p "$OUTPUT_DIR"

cat << EOF > "$FILE_PATH"
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

## Review Outcome (Gemini 3.5 Flash)
- (To be filled by agent)

## Verification
- (To be filled by agent)

## Git & Storage Outcome
- **代碼位置**: $(pwd)
- **雲端報表**: $FILE_PATH

---
*本快照由 OpenClaw Agents 手動生成，記錄技術演進。*
EOF

echo "Snapshot generated at: $FILE_PATH"
