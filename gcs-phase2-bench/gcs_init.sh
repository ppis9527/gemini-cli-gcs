#!/bin/bash
# ~/.gemini/hooks/gcs_init.sh
# GCS SessionStart Hook (Safe Implementation)

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
CHECKPOINT="$PROJECT_ROOT/.gemini/checkpoint.json"

if [ -f "$CHECKPOINT" ]; then
    # Validate JSON with jq to prevent shell escape
    if jq empty "$CHECKPOINT" >/dev/null 2>&1; then
        echo "<gcs_checkpoint_restore>"
        cat "$CHECKPOINT"
        echo "</gcs_checkpoint_restore>"
    else
        # Silent failure for security and UX
        :
    fi
fi
