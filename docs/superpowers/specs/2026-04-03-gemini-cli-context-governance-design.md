# Design Spec: Gemini CLI 上下文治理系統 (GCS) v1.5 (Final)

## 1. 核心目標
建立一套自動化的、具備預算意識的上下文管理框架，透過物理級的佈局優化、骨架化冷凝、雙重路徑鎖定與 **SessionStart 自動恢復勾子**，達成極速響應與零認知退化的開發體驗。

## 2. 五大技術支柱實作細節

### A. 分層預算與自動化恢復 (Tiered Budget & Auto-Restore)
- **Hot (20k Tokens)**: 活躍工作記憶。
- **骨架化冷凝**: 當超過限額時，執行「骨架化」處理並移入 Layer 4。
- **SessionStart Hook**: 實作自動恢復機制。透過全域 `settings.json` 配置 `SessionStart` 勾子，在每次會話啟動（或回溯重置）時，自動偵測並注入 `.gemini/checkpoint.json` 的蒸餾狀態。

### B. Prefix-safe 快取佈局 (Layout Stack)
1. **System Mandates (頂部)**
2. **Skills (靜態)**
3. **Project Manifest & Env (穩定)**
4. **Checkpoint/Skeletonized Summary (恢復層 - 由 Hook 注入)**
5. **Active Source Promotion (對齊追加區)**
6. **Ephemeral Conversation (底部)**

### C. 懶加載快取續約 (Lazy Cache Extension)
- 每次啟動偵測 TTL，剩餘 < 10min 則自動發送續約請求。

### D. 分級熔斷語義感知 (LSP with Multi-tier Timeout)
- 具備 L1/L2/L3 分級超時機制的 `universal-lsp-bridge.py`。

### E. 安全邊界與隔離驗證 (Security & Sandbox)
- **雙重 realpath 鎖定**: 強制驗證實體路徑。
- **邏輯沙盒**: 隔離 `$HOME` 與 `$TMPDIR`。

## 3. 自動化恢復邏輯
- **腳本**: `~/.gemini/hooks/gcs_init.sh`
- **行為**: 
    1. 偵測當前目錄是否具備有效檢查點。
    2. 若有，將 JSON 內容格式化為 Markdown 塊輸出。
    3. Agent 識別該輸出並自動同步內部 Pending Work 狀態。
-e 

#2026-04-04
