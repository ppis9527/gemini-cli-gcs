---
title: Universal Supply Chain Intelligence (USCI) 設計規格書
date: 2026-04-21
tags:
  - spec
  - x-tracker
  - semantic-search
  - universal-tracking
  - 2026-04-21
status: draft
---

# Universal Supply Chain Intelligence (USCI) 設計規格書

#spec #x-tracker #semantic-search #vector-db #2026-04-21

## 1. 目的 (Objective)
將現有的 CPO 專項追蹤系統升級為「全產業」通用框架。利用 **語意向量搜尋 (Semantic Search)** 取代單一關鍵字匹配，並透過 **Agentic Reasoning** 自動識別新產業、新標的及其供應鏈位置。

## 2. 核心架構變更 (Architectural Changes)

### 2.1 語意檢索層 (Semantic Layer)
- **技術選型**: 引入 `nomic-embed-text (768-dim)` 或 Google `text-embedding-004`。
- **向量存儲**: 於 `tweets.db` 旁建立 `vector_index.bin` (FAISS) 或整合 `sqlite-vss` 擴充。
- **意圖搜尋 (Intent Search)**: 搜尋關鍵字不再是 "CPO"，而是「描述企業間交易、組裝、封裝或原材料供應關係的內容」。

### 2.2 動態產業識別 (Dynamic Industry Discovery)
- **分類引擎**: 使用 Gemini 1.5 Pro 進行掃描。
- **邏輯**: 
    1. 擷取帶有「關係意圖」的推文。
    2. 由 LLM 判斷所屬產業標籤（如：Liquid Cooling, HBM, Low Earth Orbit）。
    3. 自動在 `cpo_companies` 表中擴充 `industry_tag` 欄位。

### 2.3 強化版實體對齊 (Global Entity Resolver)
- **維基整合**: Resolver 在處理未知實體時，優先查詢 Wikidata API 獲取官方 Ticker 與 Industry。
- **跨產業關聯**: 支援「A 公司在產業 X 是供應商，但在產業 Y 是客戶」的多重角色記錄。

## 3. 資料庫 Schema 擴修 (Schema Expansion)

```sql
-- 全產業重構 (Schema Generalization)
ALTER TABLE cpo_companies RENAME TO industry_entities;
ALTER TABLE cpo_supply_relations RENAME TO industry_relations;

-- 欄位擴充
ALTER TABLE industry_entities ADD COLUMN industry_tags TEXT; -- JSON array: ["CPO", "AI"]
ALTER TABLE industry_relations ADD COLUMN industry_context TEXT; -- 例如: "Cooling", "HBM"
ALTER TABLE industry_relations ADD COLUMN confidence_reason TEXT;
ALTER TABLE industry_relations ADD COLUMN evidence_snippet TEXT; -- 原始推文片段
```

## 4. 處理流程 (Workflow)
1. **Hybrid Embedding**: 歷史資料使用本地  預處理，新推文使用  API。
2. **Two-Stage Filtering**: 
   - **Stage 1 (Recall)**: 透過  進行向量召回，撈出具備「供應意圖」的候選推文。
   - **Stage 2 (Reasoning)**: 使用 Gemini 1.5 Flash 驗證關係並進行結構化萃取。
3. **Contextual Persistence**: 將關係寫入 DB，並附帶  語境標籤。
4. **Graph Refresh**: 自動更新分層圖譜與 Discord 快取。

## 5. 驗證標準 (Success Criteria)
- [ ] 能在不增加關鍵字的情況下，自動挖出「液冷散熱」或「先進封裝」的新關係。
- [ ] 支援 `/supply industry:Cooling` 指令。
- [ ] 維持 $O(1)$ 的查詢效能。

---
*Created by OpenClaw Agents.*
