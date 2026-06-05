# GCS Cross-Platform Merger Implementation Plan

This plan outlines the steps to merge the **Windows-Only** compatibility features of the `custom-session-manager` skill into the more advanced **Unix-Shared** codebase version, working inside the local sandbox workspace `/Users/yaojenliu/projects/gcs`.

## Pre-Flight Check & Workspace Sandbox Setup

1. **Verify Workspace**: Confirm `/Users/yaojenliu/projects/gcs` is the active workspace.
2. **Copy Baseline**: Copy all files from `/Users/yaojenliu/Library/CloudStorage/GoogleDrive-yaojenliu@google.com/My Drive/MyMDs/Skills_MCP_Extension/skills-source/unix-shared/custom-session-manager/` into `/Users/yaojenliu/projects/gcs/`.
3. **Initialize Git**: Initialize a git repository locally in `/Users/yaojenliu/projects/gcs/` and make an initial commit so we can easily track our modifications.

## Task 1: Cross-Platform Compatibility in `token_monitor.js`
Modify `/Users/yaojenliu/projects/gcs/gcs/token_monitor.js` to dynamically support both Unix-like and Windows platforms.

- **Target File**: `/Users/yaojenliu/projects/gcs/gcs/token_monitor.js`
- **Changes**:
  1. Add `os` module import and define platform constants:
     ```javascript
     const os = require("os");
     const HOME = os.homedir();
     const IS_WIN = process.platform === "win32";
     ```
  2. Implement non-blocking stdin safety checks:
     ```javascript
     const inputData = fs.readFileSync(0, "utf-8");
     if (!inputData) process.exit(0);
     const input = JSON.parse(inputData);
     ```
  3. Adapt file paths for `globalStatusPath` and `gdriveStatusPath` to dynamically handle Windows (`G:\` or standard directories) and Unix.
  4. Ensure UI notification commands (`tmux display-message` and MacOS `osascript` alert) are conditionally skipped when `IS_WIN` is true.
  5. Resolve Python executable dynamically: use `venv/Scripts/python.exe` on Windows and `venv/bin/python3` on Unix/Mac.
  6. Adapt `findProjectRoot()` to safely handle path traversal on Windows (using Windows root volume like `C:\` or `G:\`).

## Task 2: Code Validation & Quality Check
Perform validation checks on the modified files to ensure syntax correctness.

- **Target Files**: 
  - `/Users/yaojenliu/projects/gcs/gcs/token_monitor.js`
  - `/Users/yaojenliu/projects/gcs/lib/bootstrap.py`
  - `/Users/yaojenliu/projects/gcs/gcs/gcs_orchestrator.py`
- **Verification Steps**:
  1. Test syntax check on Node.js script: `node --check /Users/yaojenliu/projects/gcs/gcs/token_monitor.js`.
  2. Compile Python scripts: `python3 -m py_compile /Users/yaojenliu/projects/gcs/lib/bootstrap.py /Users/yaojenliu/projects/gcs/gcs/gcs_orchestrator.py`.
  3. Review the git diff to ensure changes are surgical and have zero side effects.

#csm #gcs #merger #plan #2026-06-04
