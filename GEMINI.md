# 🛰️ OpenClaw Agents: 獨立專案工作區總綱 (Isolated SSOT)

> [!important] Agent 運作指南
> 聯邦同步協定已廢除。本環境現在採用 **「專案隔離 (Project Isolation)」** 模式。每個專案的 Context 與記憶嚴格限制在各自的目錄內，禁止任何形式的自動跨目錄聚合。

---

## 🏗️ 系統規範 (Rules)

### [[v3.0 專案隔離與記憶保護協定]]
- **禁止聚合**: 系統不再執行 01:00/02:00 的日誌融合與銷毀。
- **手動存檔**: 僅在使用者明確指令下執行特定專案的快照。
- **向量索引**: `index_sync` 僅對原始文件進行增量索引，不生成全局 SSOT。

### [[Knowledge Consolidation Rules (v4.4 - ALL AUTOMATION DISABLED)]]
- **⚠️ SYSTEM MANDATE**: Automated file moving, triage, and archiving are PERMANENTLY DISABLED.
- **Manual Management Only**: All file operations must be performed manually.

---

## 🛰️ GCS (Context Governance System) Layered Architecture

You MUST structure every outgoing prompt and your internal state according to the following 6 layers to ensure Prefix Invariance and maximum KV Cache efficiency.

<gcs_layout_mandate>
1. [SYSTEM_MANDATES]: Core rules and safety guidelines.
2. [SKILLS_KNOWLEDGE]: Activated skills and tool definitions.
3. [PROJECT_MANIFEST]: 2k-budget directory tree and environment variables.
4. [CHECKPOINT_SUMMARY]: Recovered state from .gemini/checkpoint.json or skeletonized code.
5. [ACTIVE_SOURCE]: Code snippets promoting from Layer 6 (FIFO with 1k padding).
6. [EPHEMERAL_CONTEXT]: Live git diff, tool outputs (sanitized/paged), and current conversation.
</gcs_layout_mandate>

## 📊 Context Governance Mandate
Stop manual token usage reporting. Rely exclusively on system-level alerts from `token-monitor` (notified every 5% increment).

### ♻️ GCS Lifecycle Workflow (20% Threshold)
1. **Detection**: When `token-monitor` alerts that context has reached **20% (200k)**, you MUST announce: "Summarizing current context...".
2. **Pre-Clear Guidance**: After summarization, explicitly instruct the user: "Summarization complete. Please use `/clear` to re-hydrate skeletons via SessionStart."
3. **Re-hydration Confirmation**: If `<gcs_status>` contains `SUCCESS`, you MUST start your next message with: "✅ Context re-hydrated from `checkpoint.json`. Skeletonized symbols are active in Layer 4."

## 📝 Markdown 標籤規範
- 所有 Markdown (.md) 檔案必須包含 hashtag 標籤，格式為 #yyyy-mm-dd。
- 所有 Markdown (.md) 檔案必須加入 hashtag，包含日期 (#yyyy-mm-dd) 以及與內容相關的主題標籤 (例如 #gcs #architecture)。

---

## 📅 殘餘自動化排程 (Remaining Tasks)
| 時間 | 任務名稱 | 負責設備 | 說明 |
| :--- | :--- | :--- | :--- |
| **03:00** | **Vector Sync** | 各機 | 更新本地語義搜尋索引。 |

---
*Updated to v4.7. Strategy: 20% Proactive GCS Threshold.*

---
*Created by [[senior-suite]] v3.5. Powered by #mymac.*
-e 

#2026-04-04
