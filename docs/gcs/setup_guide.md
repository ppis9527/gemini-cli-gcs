# Skill Integration & Setup Guide (Custom Session Manager)

#2026-06-06 #csm #setup #guide #gcs

This guide provides simple setup steps to deploy the unified **Custom Session Manager** skill (which pre-integrates **GCS Guardian** for real-time token monitoring and background YOLO distillation) on macOS or Linux.

---

## 🛠️ Setup Steps

### 1. Place the Skill in your Global Skills Directory
Ensure the skill is checked out or copied to the standard global skills directory path:
```bash
# Path must be exactly:
~/.gemini/skills/custom-session-manager
```

---

### 2. Configure Python Virtual Environment (Venv)
The distillation engine requires Tree-sitter and language dependencies to parse code AST skeletons. Set up the virtual environment:
```bash
cd ~/.gemini/skills/custom-session-manager

# Create the virtualenv
python3 -m venv venv

# Install dependencies
./venv/bin/python3 -m pip install -r requirements.txt
```

---

### 3. Register Global hook in `~/.gemini/settings.json` (AfterModel)
> [!IMPORTANT] Hook Registration Constraint
> Due to mounting constraints in the Gemini CLI, model-level hooks (like `AfterModel`) must be registered in the **global settings file** and must use the **absolute path** to the token monitor.

1. Get the absolute path to `token_monitor.js` on your machine:
   ```bash
   echo "node $HOME/.gemini/skills/custom-session-manager/src/gcs/token_monitor.js"
   ```
   *(e.g., `node /Users/your_username/.gemini/skills/custom-session-manager/src/gcs/token_monitor.js`)*

2. Open `~/.gemini/settings.json` and add the hook using the absolute path (replacing `/Users/your_username` with your actual username):

```json
{
  "hooks": {
    "AfterModel": [
      {
        "matcher": "*",
        "hooks": [
          {
            "name": "gcs-token-monitor",
            "type": "command",
            "command": "node /Users/your_username/.gemini/skills/custom-session-manager/src/gcs/token_monitor.js"
          }
        ]
      }
    ]
  }
}
```

---

### 4. Tmux Integration
To display the real-time context usage percentage in the tmux status line, add the following to your `~/.tmux.conf`:

```tmux
# GCS Guardian — Display real-time context usage in status line
set -g status-right "#[fg=magenta]#($HOME/.gemini/skills/custom-session-manager/src/gcs/tmux_status.sh '#{session_id}')#[default] | %H:%M "
set -g status-interval 3
```

Reload your tmux configuration:
```bash
tmux source-file ~/.tmux.conf
```

---

## ⚡ Verification
1. Start a new **Gemini CLI** session in a tmux pane.
2. The bottom right status bar should light up with a purple **`[GCS: 0%]`** metric.
3. Submit any prompt. The percentage should update automatically after the model responds, verifying that the Custom Session Manager skill is fully operational.
