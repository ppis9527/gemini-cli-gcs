# 🛰️ GCS Guardian: Context Governance System (SSOT)

> [!important] GCS 運作指南 (v1.20)
> 本專案為 GCS Guardian 終極治理系統。所有 Context 與對話進度均受 L4 骨架重灌協議保護，嚴格執行 20% 閾值蒸餾監控。

---

## 🏗️ 系統規範 (System Mandates)

### [[v3.0 專案隔離與記憶保護協定]]
- **專案隔離**: Context 與記憶嚴格限制在各自的目錄內，禁止自動跨目錄聚合。
- **手動存檔**: 僅在使用者明確指令下執行特定專案的快照 (Snapshot)。
- **向量索引**: `index_sync` 僅對原始文件進行增量索引。

---

## 🛰️ GCS (Context Governance System) Layered Architecture

所有 Prompt 與內部狀態必須遵循以下 6 層佈局，以確保前綴不變性 (Prefix Invariance) 與最大化 KV Cache 效率。

<gcs_layout_mandate>
1. [SYSTEM_MANDATES]: 核心規則、安全指南與 GCS 操作規範。
2. [SKILLS_KNOWLEDGE]: 已啟動的 Agent 技能與工具定義。
3. [PROJECT_MANIFEST]: 2k 預算內的專案目錄樹與環境變量。
4. [CHECKPOINT_SUMMARY]: 由 gcs_init.sh 從 .gemini/checkpoint.json 注入的骨架化代碼。
5. [ACTIVE_SOURCE]: 當前涉及的完整檔案內容 (4096B 桶對齊)。
6. [EPHEMERAL_CONTEXT]: 即時 Git Diff、最近對話歷史與臨時工具輸出。
</gcs_layout_mandate>

## 📊 治理指標與閾值 (Context Governance Mandate)

### ♻️ GCS 生命週期流程 (20% 閾值)
1. **偵測 (Detection)**: 當 `token_monitor.js` 偵測到 Token 使用率達到 **20% (4M / 20M)** 時，自動啟動背景蒸餾。
2. **預警 (Alert)**: 當飽和度達到 80% 時，顯示通知要求使用者執行 `/clear`。
3. **續行 (Resume)**: 使用者輸入 `/clear` 後，`gcs_init.sh` 讀取 `checkpoint.json` 重灌 L4 骨架並恢復任務狀態。

---

## 📝 Markdown 標籤規範
- 所有 Markdown (.md) 檔案必須包含當天日期的 hashtag 標籤 (#yyyy-mm-dd)。
- 所有 Markdown (.md) 檔案必須包含與內容相關的主題標籤 (例如 #gcs #architecture)。

---
*Updated to v4.8. GCS Guardian Ultimate SSOT.*
-e 

#2026-04-07 #gcs #architecture #ssot
