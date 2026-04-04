#!/bin/bash
# ~/.gemini/hooks/gcs_init.sh
# GCS SessionStart Hook (Branch-Aware Implementation)

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$PROJECT_ROOT" ]; then
    PROJECT_ROOT=$(pwd)
fi

# 0. Tool check (silent skip if missing)
command -v jq >/dev/null 2>&1 || exit 0

CHECKPOINT="$PROJECT_ROOT/.gemini/checkpoint.json"

if [ -f "$CHECKPOINT" ]; then
    # 0. Check for jq dependency
    if ! command -v jq >/dev/null 2>&1; then
        # echo "GCS: jq not found. Skipping restoration."
        exit 0
    fi

    # 1. Validate JSON
    if ! jq empty "$CHECKPOINT" >/dev/null 2>&1; then
        exit 0
    fi

    # 2. Verify Commit SHA (Branch-Aware Safety)
    CURRENT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "no-git-repo")
    CHECKPOINT_SHA=$(jq -r '.commit_sha' "$CHECKPOINT")

    if [ "$CURRENT_SHA" != "$CHECKPOINT_SHA" ]; then
        # Branch/Commit changed - ignore stale checkpoint to prevent context poisoning
        # echo "GCS: Stale checkpoint detected. Skipping."
        exit 0
    fi

    # 3. Output L4 Injection Block
    echo "<gcs_checkpoint_restore>"
    cat "$CHECKPOINT"
    echo "</gcs_checkpoint_restore>"
    echo "<gcs_status>SUCCESS: Checkpoint Re-hydrated via SessionStart (clear)</gcs_status>"
    
    # 4. Success Log in GCS log
    LOG_PATH="$PROJECT_ROOT/.gemini/gcs.log"
    echo "[$(date)] SessionStart: Successfully restored context for $CURRENT_SHA" >> "$LOG_PATH"
fi
