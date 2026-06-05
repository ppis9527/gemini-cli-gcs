# Implementation Plan: Remote Guardian System
#2026-05-14

## Objective
Implement a decoupled monitoring and repair system to track the health of a remote gLinux Cloudtop from a local gMac tmux session, using Google Drive as a synchronization layer.

## Context & Research
- **Design Doc**: `/Users/yaojenliu/Library/CloudStorage/GoogleDrive-yaojenliu@google.com/My Drive/MyMDs/Skills_MCP_Extension/skills-source/unix-shared/remote-guardian/DESIGN.md`
- **Remote Host**: `yaojenliu-10.c.googlers.com`
- **Status File**: `MyMDs/.remote_status` (JSON)
- **Sync Mechanism**: Google Drive / CloudStorage.

## Pre-Flight Check / Workspace Cleanup
1. **Status**: Verify `~/scripts/` directory exists on both gLinux and gMac.
2. **Dependencies**: Ensure `jq` and `fzf` are available.
3. **Connectivity**: Confirm passwordless SSH to `yaojenliu-10.c.googlers.com`.

---

## Task 1: Remote Reporter (gLinux)
**To be executed by Implementer**

- **Target**: `~/scripts/remote_guardian.sh`
- **Logic**:
    - Get gcert TTL: `gcertstatus --check_ssh --format=json | jq .ttl`
    - Check DriveFS: `[ -d "/google/src/cloud/yaojenliu/MyMDs" ] && echo "OK" || echo "DOWN"`
    - Count tasks: `pgrep -f "md2gdoc" | wc -l`
    - Load avg: `awk '{print $1}' /proc/loadavg`
- **Verification**: Run manually and verify `.remote_status` JSON.
- **Automation**: `crontab -e` -> `*/5 * * * * ~/scripts/remote_guardian.sh`.

---

## Task 2: Local Indicator (gMac)
**To be executed by Implementer**

- **Target**: `~/scripts/tmux_remote_indicator.sh`
- **Logic**:
    - Read `.remote_status` from local GDrive path.
    - Status Logic:
        - `CRITICAL` (Red): gcert <= 0 or DriveFS == "DOWN".
        - `WARNING` (Yellow): gcert < 2h or tasks > 0.
        - `OK` (Green): Otherwise.
    - Output: Tmux color strings.
- **Verification**: Run with mock JSON data.

---

## Task 3: Local Dashboard (gMac)
**To be executed by Implementer**

- **Target**: `~/scripts/tmux_remote_dashboard.sh`
- **Logic**:
    - Use `fzf` to show details.
    - Actions Menu:
        - `Renew gcert`: `ssh yaojenliu-10.c.googlers.com 'gcert'`
        - `Restart DriveFS`: `ssh yaojenliu-10.c.googlers.com 'drivefs_restart'`
        - `Kill Tasks`: `ssh yaojenliu-10.c.googlers.com 'pkill -f md2gdoc'`
- **Verification**: Open popup and trigger actions.

---

## Task 4: Tmux Integration (gMac)
**To be executed by Implementer**

- **Target**: `~/.tmux.conf`
- **Changes**:
    - `set -g status-right "... #(~/scripts/tmux_remote_indicator.sh) ..."`
    - `bind-key G display-popup -E "~/scripts/tmux_remote_dashboard.sh"`
- **Verification**: Reload tmux and test hotkey.

---

## Verification Strategy
- **End-to-End**: Ensure status color changes correctly when remote state changes.
- **Interactive**: Verify repair actions successfully resolve issues on the remote host.
