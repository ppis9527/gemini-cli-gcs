#!/bin/bash

SESSION_ID="${1:-}"
if [ -z "$SESSION_ID" ]; then
    SESSION_ID=$(tmux display-message -p -F '#{session_id}' 2>/dev/null || echo "no-tmux")
fi

STATUS_FILE="$HOME/.gemini/gcs-guardian/sessions/$SESSION_ID/tmux_status"
if [ -f "$STATUS_FILE" ]; then
    cat "$STATUS_FILE"
else
    echo "[GCS: --]"
fi
