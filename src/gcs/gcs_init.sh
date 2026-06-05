#!/bin/bash
# GCS Guardian SessionStart Hook (Hardened v1.5)

SESSION_ID=$(tmux display-message -p -F '#{session_id}' 2>/dev/null || echo "no-tmux")
SESSION_DIR="$HOME/.gemini/gcs-guardian/sessions/$SESSION_ID"

# Reset tmux status for the active tmux session
mkdir -p "$SESSION_DIR"
echo "[GCS: 0%]" > "$SESSION_DIR/tmux_status"

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$PROJECT_ROOT" ]; then
    # SD-003: Closest Anchor Law
    CUR=$(pwd)
    for i in {1..5}; do
        if [ -d "$CUR/.git" ] || [ -f "$CUR/GEMINI.md" ]; then
            PROJECT_ROOT="$CUR"
            break
        fi
        CUR=$(dirname "$CUR")
        if [ "$CUR" == "/" ] || [ "$CUR" == "$HOME" ]; then break; fi
    done
fi

if [ -z "$PROJECT_ROOT" ]; then exit 0; fi

CHECKPOINT="$PROJECT_ROOT/.gemini/checkpoint.json"
PENDING="$PROJECT_ROOT/.gemini/gcs.pending"
LOG="$PROJECT_ROOT/.gemini/gcs.log"

# Task 5 Step 1: WAS Recovery
if [ -f "$PENDING" ]; then
    echo "<gcs_resume_signal>"
    cat "$PENDING"
    echo "</gcs_resume_signal>"
    rm -f "$PENDING" # Consume the signal
fi

# Task 5 Step 2: In-memory/Checkpoint Restoration
if [ -f "$CHECKPOINT" ]; then
    # Basic size validation
    SIZE=$(wc -c <"$CHECKPOINT")
    if [ $SIZE -gt 5242880 ]; then exit 0; fi # 5MB Gate

    echo "<gcs_checkpoint_restore>"
    cat "$CHECKPOINT"
    echo "</gcs_checkpoint_restore>"
    echo "<gcs_status>SUCCESS: Context Re-hydrated</gcs_status>"
fi

# Log Rotation (SD-005)
if [ -f "$LOG" ] && [ $(wc -c <"$LOG") -gt 5242880 ]; then
    mv "$LOG" "$LOG.old"
    touch "$LOG"
fi
