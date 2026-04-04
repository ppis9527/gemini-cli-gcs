---
title: Notion Skill 開發歷程與 v4.0 使用手冊 — 終極技術指南 (SSOT)
tags: [notion, api, automation, skill, node-js, setup, SSOT]
date: 2026-03-07
status: 🏆 Refined (Lossless Preservation)
---

# 📓 Notion Skill：開發進化與 v4.0 完整手冊

> [!abstract] 核心定義
> 本文件為 Notion 同步工具的唯一真理來源 (SSOT)。彙整了從 v4.0 模組化架構、各項管理指令、到最新 `get-options` 動態查詢功能的全部技術細節與操作範例。

---

## 🏗️ 第一部分：Notion Skill v4.0 簡介

Notion Skill v4.0 採用模組化架構，將功能拆分為獨立指令模組，主要用於將 OpenClaw 的任務與報告同步至 **ErXia Hub 2.0** Dashboard。

- **核心腳本位置**: `~/.openclaw/workspace/skills/notion/scripts/notion-sync.js`

---

## 🚀 第二部分：常用指令手冊 (Command Reference)

### 1. 查詢任務 (Query)
列出所有項目或根據狀態/類型/名稱進行篩選：
```bash
node notion-sync.js query                           # 列出所有項目
node notion-sync.js query "⏳ 進行中 (In Progress)" # 篩選「進行中」
node notion-sync.js query "未開始" "Task"           # 篩選特定狀態 + 類型
node notion-sync.js query --name "任務標題"         # 根據名稱精確查詢
```

### 2. 建立與更新任務 (Manage)
```bash
# 建立任務: task <標題> <Agent> <優先級> <狀態>
node notion-sync.js task "重構認證邏輯" "貳俠" "High" "進行中"

# 更新任務狀態: update <page-id> <新狀態>
node notion-sync.js update "your-page-id-here" "已完成"
```

### 3. 同步報告與刪除項目 (Ops)
```bash
# 同步使用報告: report <標題> <Agent>
node notion-sync.js report "[AUTO] 每週統計" "Gemini"

# 刪除/歸檔項目: delete <page-id>
node notion-sync.js delete "your-page-id-here"
```

### 4. 查詢屬性選項 (Dynamic Inspection)
列出 Select、Multi-select 或 Status 屬性的所有可能選項：
```bash
node notion-sync.js get-options "Status"
node notion-sync.js get-options "Agent"
node notion-sync.js get-options "Priority"
```

---

## 🧠 第三部分：技術開發紀錄 (get-options 進化)

### 1. 任務描述與需求
為了讓下游腳本能動態適應 Notion 資料庫的變動，開發了 `get-options` 命令。
- **端點**: 使用 `Retrieve a database` (GET `/v1/databases/{database_id}`)。
- **邏輯**: 解析 `properties` 欄位以提取 `select`、`multi_select` 或 `status` 的選項列表。

### 2. 關鍵決策與實作細節
- **多類型支援**: 完整支援 Notion 中最常見的「狀態」與「選擇」標籤。
- **輸出格式彈性**: 支援 `FORMAT=json` 環境變數，讓輸出可在「每行一項」與「標準 JSON 陣列」間切換。
- **安全認證**: 延用 `getApiKey()` 邏輯，優先從 GCP Secret Manager (`NOTION_OPENCLAW_KEY`) 獲取金鑰。

---

## 📋 第四部分：資料庫標準 (ErXia Hub 2.0)

當使用此 Skill 時，以下欄位會自動管理：
- **Name**: 條目名稱。
- **Type**: 根據動作自動設定（`Task` 或 `Report`）。
- **Agent**: 映射至 `貳俠` (Claude Code)、`小序` (Claude TG)、`Gemini` 或 `Claude`。
- **Priority**: (僅限任務) `High`, `Medium`, 或 `Low`。
- **Status**: 任務狀態（例如：`進行中`, `已完成`, `未開始`）。

---
*遵循 Rule-1：全量資訊保留。合併自 notion-skill-v4-manual 及 notion-skill-get-property-options。*
*Produced by [[senior-suite]] v3.5.*
-e 

#2026-04-04
