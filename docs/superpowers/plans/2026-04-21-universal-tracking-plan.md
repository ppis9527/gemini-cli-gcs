# Universal Supply Chain Intelligence (USCI) 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 透過語意向量搜尋與雙階 LLM 驗證，將 X-Tracker 升級為支援全產業供應鏈自動識別與追蹤的智慧系統。

**Architecture:** 
1. 向量庫：使用 `sqlite-vec` 整合至現有 `tweets.db`。
2. 流程：Vector Search (Recall) -> LLM Extraction (Reasoning) -> Knowledge Graph (Persistence)。
3. 語境化：引入 `industry_context` 確保跨產業關係的精確性。

**Tech Stack:** Python 3.14, SQLite (with sqlite-vec extension), Gemini 1.5 Flash/Pro, sentence-transformers (local embedding).

---

### Task 1: 基礎設施升級 - 向量資料庫整合

**Files:**
- Create: `cpo_chain/vec_db.py`
- Modify: `cpo_chain/db.py`
- Test: `tests/test_vec_db.py`

- [ ] **Step 1: 安裝 sqlite-vec 並擴充資料表**
```python
import sqlite3

def init_vector_tables(conn):
    # 確保 sqlite-vec 載入 (假設已安裝編譯好的擴充功能)
    # 建立向量表儲存推文 Embedding
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS tweet_embeddings USING vec0(
            tweet_id INTEGER PRIMARY KEY,
            embedding FLOAT[768] -- 假設使用 384 維本地模型
        );
    """)
```

- [ ] **Step 2: 執行 Schema 重構與遷移**
```bash
# 重新命名舊表
sqlite3 tweets.db "ALTER TABLE cpo_companies RENAME TO industry_entities;"
sqlite3 tweets.db "ALTER TABLE cpo_supply_relations RENAME TO industry_relations;"
# 增加產業與語境欄位
sqlite3 tweets.db "ALTER TABLE industry_entities ADD COLUMN industry_tags TEXT;"
sqlite3 tweets.db "ALTER TABLE industry_relations ADD COLUMN industry_context TEXT;"
sqlite3 tweets.db "CREATE UNIQUE INDEX IF NOT EXISTS idx_rel_context ON industry_relations(from_company_id, to_company_id, industry_context);"
```

### Task 2: 混合 Embedding 流水線實作

**Files:**
- Create: `cpo_chain/embedder.py`
- Test: `tests/test_embedder.py`

- [ ] **Step 1: 實作本地冷啟動 Embedder**
使用 `all-MiniLM-L6-v2` 處理歷史推文，並存入 `tweet_embeddings` 表。

### Task 3: 雙階萃取邏輯 (Recall -> Reasoning)

**Files:**
- Modify: `cpo_chain/extract_cpo.py` (Rename to `extract_universal.py`)

- [ ] **Step 1: 實作向量召回 (Stage 1)**
輸入意圖描述語句，從 `sqlite-vec` 撈回前 100 筆推文。

- [ ] **Step 2: 整合 LLM 語境驗證 (Stage 2)**
將召回結果送交 Gemini，識別具體產業與關係，並寫入 `industry_relations`。

### Task 4: Discord 全產業指令升級

**Files:**
- Modify: `discord_bot.py`

- [ ] **Step 1: 新增 /supply 指令**
支援 `/supply industry:HBM` 等全產業查詢，底層串接 `industry_relations` 與 `industry_context`。

---
*Self-Review: 計畫涵蓋了從向量庫到底層 Schema 的全面遷移，並設計了雙階驗證防止數據污染。*

### Task 5: 強化實體對齊 - Wikidata 整合

**Files:**
- Modify: 

- [ ] **Step 1: 實作 Wikidata API 回退機制**
當本地快取找不到實體時，自動透過 Wikidata 查詢該公司的 Ticker 與官方產業標籤，減少人工審核負擔。
