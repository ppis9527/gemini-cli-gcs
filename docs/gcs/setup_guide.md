# 🛰️ GCS Guardian 保姆級安裝與設定指南 (Traditional Chinese)

#2026-05-18 #gcs #setup #guide #doc #infra

本指南提供從零開始在全新電腦（macOS / Linux）部署 **GCS Guardian (v1.22.0)** 的完整步驟，以確保 Token 監控、Tmux 狀態欄與背景 YOLO 蒸餾能完美運作。

---

## 🛠️ 安裝步驟

### 1. 同步最新程式碼與目錄部署
在終端機執行以下指令，建立全域擴充套件資料夾，並將最新修復的 Repo 複製到指定路徑下：

```bash
# 確保建立全域擴充套件目錄
mkdir -p ~/.gemini/extensions

# 將 Repo 複製到指定目錄下 (名稱必須是 gcs-guardian)
git clone https://github.com/ppis9527/gemini-cli-gcs.git ~/.gemini/extensions/gcs-guardian
```
*(註：若您已經 Clone 過，請進入該目錄執行 `git pull` 確保取得 `process.env.HOME` 動態路徑修復版。)*

---

### 2. 建立 Python AST 虛擬環境 (Venv)
GCS 需要 Tree-sitter 來解析代碼 AST 骨架。請執行專案內附的安裝腳本：

```bash
# 進入目錄並執行安裝環境腳本
cd ~/.gemini/extensions/gcs-guardian
bash src/gcs/setup.sh
```
*這會自動建立 `~/.gemini/extensions/gcs-guardian/.gemini/gcs-venv`，並自動安裝 Tree-sitter 與語言相關的依賴包。*

---

### 3. 將執行腳本與軟連結設定複製到位
為了讓 Hook 順利讀取，請手動複製核心腳本並給予權限：

```bash
# 1. 建立 scripts 資料夾
mkdir -p ~/.gemini/extensions/gcs-guardian/scripts

# 2. 將核心腳本複製過去
cp src/gcs/token_monitor.js ~/.gemini/extensions/gcs-guardian/scripts/
cp src/gcs/tmux_status.sh ~/.gemini/extensions/gcs-guardian/scripts/
cp src/gcs/gcs_init.sh ~/.gemini/extensions/gcs-guardian/scripts/
cp src/gcs/gcs_orchestrator.py ~/.gemini/extensions/gcs-guardian/scripts/
cp src/gcs/gcs_distiller.py ~/.gemini/extensions/gcs-guardian/scripts/
cp src/gcs/config.py ~/.gemini/extensions/gcs-guardian/scripts/

# 3. 確保 python 虛擬環境軟連結位置正確
ln -s ~/.gemini/extensions/gcs-guardian/.gemini/gcs-venv ~/.gemini/extensions/gcs-guardian/venv

# 4. 給予腳本可執行權限
chmod +x ~/.gemini/extensions/gcs-guardian/scripts/gcs_init.sh
chmod +x ~/.gemini/extensions/gcs-guardian/scripts/token_monitor.js
chmod +x ~/.gemini/extensions/gcs-guardian/scripts/tmux_status.sh
```

---

### 4. 註冊 `extension.json` (SessionStart)
建立並編輯 `~/.gemini/extensions/gcs-guardian/extension.json`，讓開局重灌與 Tmux 0% 初始化機制生效：

```json
{
  "name": "gcs-guardian",
  "version": "1.22.0",
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "bash ~/.gemini/extensions/gcs-guardian/scripts/gcs_init.sh"
      }
    ]
  }
}
```

---

### 5. 註冊全域 `~/.gemini/settings.json` (AfterModel)
> [!IMPORTANT] 核心綁定限制
> 由於 Gemini CLI 底層模組掛載限制，模型等級 Hook（如 `AfterModel`）必須寫在**全域設定檔**中，且必須寫死您當前電腦的**絕對路徑**（Node.js 不會解析 `~` 符號）。

1. 先在終端機輸入這行指令，取得您這台電腦的**全域絕對路徑**：
   ```bash
   echo "node $HOME/.gemini/extensions/gcs-guardian/scripts/token_monitor.js"
   ```
   *（終端機輸出類似：`node /Users/your_username/.gemini/extensions/gcs-guardian/scripts/token_monitor.js`）*

2. 打開並編輯 `~/.gemini/settings.json`，填入以下 JSON（**請將下方的 `/Users/yj` 替換為您在第 1 步取得的絕對路徑**）：

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
            "command": "node /Users/yj/.gemini/extensions/gcs-guardian/scripts/token_monitor.js"
          }
        ]
      }
    ]
  }
}
```

---

### 6. 整合 Tmux 狀態欄
編輯您電腦的 `~/.tmux.conf`，加入會依照目前 tmux session 自動切換的狀態欄：

```tmux
# GCS Guardian — 下方狀態列即時顯示 context 使用率
set -g status-right "#[fg=magenta]#($HOME/.gemini/extensions/gcs-guardian/scripts/tmux_status.sh '#{session_id}')#[default] | %H:%M "
set -g status-interval 3
```

然後在 tmux 中重新載入設定即可：
```bash
tmux source-file ~/.tmux.conf
```

---

## ⚡ 驗證是否成功
1. 打開一個全新的 **Gemini CLI**。
2. 您的 Tmux 最右下角應該會亮起紫色的 **`[GCS: 0%]`**。
3. 嘗試隨意發送一個提示詞 (Prompt)，當模型回覆後，該百分比會依據模型 API 回傳的精確 `promptTokenCount` 進行即時更新，即代表 GCS Guardian 已經成功在您新的電腦上安家落戶！
