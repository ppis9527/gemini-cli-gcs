# Spec: GCS Guardian 全域上下文治理擴充功能 v1.15

## 1. 願景與目標 (Mission)
將專案級的 GCS 邏輯提升為全域擴充功能 (`~/.gemini/extensions/gcs-guardian`)。達成「20% 自動報警、YOLO 模式下自動蒸餾與重置、重啟後精確續行」的工業級開發體驗。

---

## 2. 系統架構 (Architecture)

### 2.1 組件封裝 (Encapsulation)
- **Guardian Core**: 遷移 `src/gcs/` 下的 Python 核心邏輯至全域目錄，作為所有專案的治理引擎。
- **Context Monitor (JS)**: 將 `token-monitor-v35-proactive.js` 封裝為 Extension Hook，支援每 5% 的 stderr 顯性通知。
- **Auto-Cycle Hook (Shell/JS)**: 實作與 Gemini CLI Lifecycle 深度整合的觸發器。

### 2.2 治理流程圖 (Lifecycle Workflow)
```mermaid
graph TD
    Start[Agent Action] --> Monitor[Token Monitor: PostToolCall]
    Monitor --> |< 20%| Notify[5% Incremental stderr Alert]
    Monitor --> |>= 20%| Threshold[Governance Trigger]
    
    Threshold --> |Non-YOLO| Manual[Alert: Summarizing... Please /clear]
    Threshold --> |YOLO| Auto[Auto-Distill & SESSION_RESET]
    
    Auto --> Distill[Update checkpoint.json]
    Distill --> Reset[CLI internal /clear signal]
    
    Reset --> SessionStart[SessionStart Hook]
    SessionStart --> Rehydrate[Inject checkpoint.json to Layer 4]
    Rehydrate --> Resume[Resume Action]
    
    Resume --> |Non-YOLO| Ask[Agent asks: "We are at Step N, continue?"]
    Resume --> |YOLO| Exec[Automatic hidden prompt: "Resuming Task X"]
```

---

## 3. YOLO 模式自動續行機制 (Option B: Seamless Resume)

### 3.1 斷點錄製 (Breakpoint Recording)
在觸發自動 `/clear` 之前，GCS Guardian 會：
- **Wait for Tools**: 校驗是否有進行中的背景工具。若有，延遲 500ms 重試直到清空，防止重置導致資源洩漏。
- **Serialize State**: 將目前的 **`active_task`**、**`pending_work`** 與 **`current_step_id`** 序列化。

### 3.2 顯性通知與隱性注入
當 Session 重啟後：
- **隱性注入 (Injected Prompt)**：
  ```markdown
  System Message: Context summarized at 20%.
  Current State: [Resume Plan Path if exists] | [Active Task if exists].
  Instruction: Resuming next sub-task. If no plan detected, ask user for next objective.
  ```

### 4.5 依賴管理與自我校驗 (Global Setup)
- **Dependency Guard**: Extension 啟動時會檢查 `~/.gemini/extensions/gcs-guardian/venv` 是否存在。若缺失，應透過 `stderr` 提示用戶執行 `setup.sh`。
- **Auto-Installation**: 提供 `setup.sh` 自動建立 venv 並安裝 `tree-sitter-python/javascript/typescript` 依賴，確保全域環境隔離。

### 4.8 安全增強、遞迴防護與熔斷機制 (Hardening & Circuit Breaker)
- **Fidelity Level 0 (Extreme Skeletonization)**: 
    - 在 Lean Mode 下，非 `active_task` 檔案僅保留 **頂級 `Import`、類別名與函數簽名**，徹底移除主體與 Docstrings，確保 Symbol Table 完整而不佔用 Token。
- **Atomic Write & In-memory Mirror**: 
    - `checkpoint.json` 更新必須執行 `Write-to-Temp -> Flush -> OS Atomic Rename`。
    - 啟動時將 Checkpoint 載入記憶體單例 (In-memory Mirror)。`PostToolCall` 需進行 Watchdog 檢查，若物理檔案意外遺失，自動從記憶體重建或鎖定 Session，防止破壞實體源碼。
- **Complexity & Time-out Gate**: 
    - 單一檔案 AST 節點數 > 30,000、嵌套深度 > 100 或解析耗時 > 200ms 時，立即觸發熔斷。
    - 熔斷後自動降級為 `head -n 25` 的位元級截斷摘要。
- **AST-level Secret Scrubbing**:
    - Distiller 必須對所有字串字面量進行高熵偵測。任何賦值給 `API_KEY`、`TOKEN`、`PASSWORD` 或符合 PEM 格式的全局/類別屬性，強制替換為 `[REDACTED]`。
- **Massive Mono-repo Protection (Sparse Monitoring)**:
    - 所有的 `git` 操作（如 `rev-parse`）必須加上 300ms 硬性超時。
    - 僅針對 `active_task` 所在的局部子目錄進行增量掃描，禁止對根目錄執行深度遞迴。
- **I/O Isolation**:
    - GCS Hook 的所有輸出必須嚴格重定向至 `.gemini/gcs.log`。發生異常時僅回傳簡潔的錯誤碼，嚴禁 Traceback 污染主 CLI 的 `stdout`/`stderr` 而導致 Token 洩漏。
- **Infinite Reset Prevention (Lean Mode)**: 
    - 若 20% 重置後初始 Token 仍超標，自動切換至 Lean Mode。
    - 動態調升門檻至 `max(20%, current_skeleton_size * 1.5)`，硬上限 50%。



---

## 4. 關鍵技術實作 (Key Implementation)

### 4.1 全域 Hook 配置 (`extension.json` / `hooks.json`)
- **正式勾子名稱**: 根據系統規範，工具執行後的勾子應正名為 **`AfterTool`**。
- **註冊結構**:
```json
{
  "name": "gcs-guardian",
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "/absolute/path/to/gcs_init.sh"
      }
    ],
    "AfterTool": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "name": "token-monitor",
            "type": "command",
            "command": "/absolute/path/to/token_monitor.js"
          }
        ]
      }
    ]
  }
}
```

### 4.2 漂移、SHA 驗證與靜默失敗 (Silent Fail)
- **Git Check**: `gcs_init.sh` 必須優先執行 `git rev-parse --is-inside-work-tree`。若回傳 false，則立即以 `exit 0` 結束，不輸出任何內容，確保非專案環境下的無感運行。
- **Commit SHA Check**: 全域 Extension 必須校驗當前目錄的 `git rev-parse HEAD` 與 `checkpoint.json` 是否一致。
- **Drift Protection**: 若檢測到 SHA 不符，自動降級為「新專案初始化」模式，防止注入錯誤骨架。

---

## 5. 驗證成功標準 (Success Criteria)
1. **全域生效**：在任何具備 Git 的目錄開啟 CLI，`token-monitor` 必須自動運作。
2. **YOLO 閉環**：模擬 20% 門檻，驗證系統能否在不需人為輸入的情況下完成 `/clear` 並自動告知下一個動作。
3. **無感延遲**：蒸餾與重灌的總耗時必須 < 200ms。

-e 

#2026-04-04 #gcs #architecture #extension #design
