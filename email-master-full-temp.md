---
title: Email Triage 自動化整理 — 終極技術與維運手冊 (SSOT)
tags: [email, gmail, triage, automation, gemini, gog, setup, SSOT]
date: 2026-03-07
status: 🏆 Refined (Lossless Preservation)
---

# 📧 Email Triage：Gmail 大量郵件自動化整理指南

> [!abstract] 核心定義
> 本文件為 Gmail 自動化整理系統的唯一真理來源 (SSOT)。彙整了從 20,000 封郵件的大規模分流架構、小序 (xiaoxu.sh) 混合規則引擎實作、到關鍵 Shell 腳本 Bug 修復的全部細節。

---

## 🏗️ 第一部分：分層處理流程架構 (v2)

為了處理約 20,000 封 Gmail 郵件，系統採用了分層過濾策略：

```text
20,000 封郵件
    ↓
Phase 1: 自動規則 (AUTO_ARCHIVE_PATTERNS) - 匹配系統通知與 Newsletter
    ↓
Phase 2: 舊郵件清理 - 365 天以前且已讀的郵件 → Archive
    ↓
Phase 3: LLM 輔助分類 - 每 50 封一組，由 LLM 決定 ARCHIVE / STAR / KEEP / DELETE
```

---

## 🛠️ 第二部分：核心腳本與指令手冊

### 1. `email-triage.sh` (大量清理專用)
**位置**: `~/.openclaw/workspace/tools/email-triage.sh`

```bash
# 預覽統計
./email-triage.sh --dry-run
# 執行自動規則 (Phase 1)
./email-triage.sh --phase1
# 產生 LLM 批次檔
./email-triage.sh --batch
# 執行全部流程
./email-triage.sh --all
```

### 2. `email-triage-xiaoxu.sh` (小序自動整理)
**位置**: `~/.openclaw/workspace/tools/email-triage-xiaoxu.sh`
**特色**: 採用「規則引擎 + LLM 混合分類」策略，規則處理了約 71% 的郵件，大幅降低 Token 成本。

#### 四階段 Pipeline
- **Stage 1**: `gog fetch metadata` (零 Token)。
- **Stage 2**: 規則引擎（過濾開發者平台、促銷標籤、驗證碼）。
- **Stage 3**: Gemini `flash-lite` 批次分類（每批 50 封）。
- **Stage 4**: 執行 `gog gmail thread modify` 並產出摘要。

---

## 🧠 第三部分：技術開發與 Bug 修復紀錄

### 1. 關鍵 Bug 診斷 (2026-03-07)
- **問題**: `grep -cP` 在無匹配項時回傳 Exit Code 1，在 `set -e` 下導致腳本中斷，並引發 `integer expression expected` 錯誤。
- **修復方案**: 
    - 將 `grep -cP` 改為 `grep -P | wc -l` (後者始終回傳 0)。
    - 在 Stage 4 的關鍵指令後補上 `|| true` 異常保護。
    - 為 `gemini` 指令強制加入 `< /dev/null` 避免 stdin 阻塞。

### 2. 實測數據參考 (2026-03-04)
- **總量**: 200 封郵件。
- **規則分類**: 142 封 (71%)。
- **LLM 分類**: 58 封 (29%)。
- **執行時間**: ~7 分鐘。
- **標星類型**: 包含銀行帳單、交易所通知、Supabase 暫停通知等重要郵件。

---

## 🔐 第四部分：認證與安全性

- **OAuth**: 透過 `gog auth add` 使用 `client_secret.json`。
- **GCP Secret Manager**: 存取 `GOG_KEYRING_PASSWORD` 以自動解鎖 Keyring。
- **隱私規範**: 腳本內嚴禁硬編碼密碼，由環境變數傳遞。

---
*遵循 Rule-1：全量資訊保留。合併自 email-triage-workflow, rerun 及 xiaoxu 系列。*
*Produced by [[senior-suite]] v3.5.*
-e 

#2026-04-04
