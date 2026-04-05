# GCS Guardian 全域擴充功能實作計畫 (v1.5 Integrity)

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 封裝具備工具感知與協作能力的 GCS 全域擴充功能，解決骨架化代碼的編輯衝突。

**Architecture:** 導入「編輯意圖感知重灌」與「協作式勾子註冊」機制。

**Tech Stack:** Node.js, Python 3.x (Isolated venv), Zlib (RFC 1950).

---

### Task 1: 全域目錄建置與路徑霸權 (Setup & Path Isolation)

- [ ] **Step 1: 建立全域目錄結構並實作路徑預檢**
- [ ] **Step 2: 編寫 `setup.sh` 實作依賴安裝與二進制檔硬化**
  - [ ] 強制使用 `/path/to/venv/bin/python3 -I` 執行環境。
  - [ ] 執行時重構純淨 `env`，清空 `PATH` 以防環境中毒 (SD-004)。
- [ ] **Step 3: 初始化 `extension.json` (協作式雙層巢狀結構)**

---

### Task 2: 蒸餾引擎與資源調度 (Distiller & Scheduling)

- [ ] **Step 1: 遷移 `gcs_distiller.py` 並實作 Secret Scrubbing**
- [ ] **Step 2: 實作進程優先級控管 (AD-003)**
  - [ ] 在引擎啟動時呼叫 `os.nice(10)` 以降低大規模掃描時的系統負擔。
- [ ] **Step 3: 實作 Fidelity Level 0 與通訊靜默協定**

---

### Task 3: 原子化寫入與跨語言一致性 (Atomic & Cross-Runtime)

- [ ] **Step 1: 實作 Atomic Write 邏輯與磁碟預檢**
- [ ] **Step 2: 實作無碟生存模式與 Zlib 標準化 (AD-004)**
  - [ ] 鎖定 **RFC 1950 (Zlib)** 標準與 **windowBits: 15**。
  - [ ] 確保 Node.js 與 Python 雙向解碼一致。
- [ ] **Step 3: 實作 In-memory Mirror 與階梯式狀態機**

---

### Task 4: 預寫式狀態與安全 YOLO (Token Monitor WAS)

- [ ] **Step 1: 實作模型動態感知與 5% 通知**
- [ ] **Step 2: 實作預寫式狀態 (WAS) 與背景任務輪詢**
- [ ] **Step 3: 實作最接近錨點法則與護欄 (SD-003)**

---

### Task 5: 編輯意圖感知與自動重灌 (Intent-Aware Re-hydrate)

- [ ] **Step 1: 實作 `prePrompt` / `preToolCall` 攔截器 (AD-001)**
  - [ ] 偵測對 `replace` 工具的調用。
  - [ ] 若目標檔案處於骨架化狀態，自動觸發 **全量回填 (Full Re-hydrate)** 供給 Agent 完整 Context 以便匹配 `old_string`。
- [ ] **Step 2: 實作 WAS 恢復與 I/O 隔離**
- [ ] **Step 3: 實作日誌輪轉 (5MB, 3 backups)**

---

### Task 6: 協作式全域註冊 (Cooperative Registration)

- [ ] **Step 1: 實作 `settings.json` 合併邏輯 (AD-002)**
  - [ ] 使用 `jq` 或 Python 指令式合併，而非覆蓋現有的 `hooks` 設定。
- [ ] **Step 2: 替換 `extension.json` 中的絕對路徑**
- [ ] **Step 3: 清理舊有的專案級腳本**

---

### Task 7: 最終驗證與編輯衝突測試 (Conflict Testing)

- [ ] **Step 1: 模擬對「骨架化函數」執行 `replace` 指令**
  - [ ] 驗證攔截器是否成功觸發重灌並讓編輯成功。
- [ ] **Step 2: 驗證與其他擴充功能並存時的 Hook 鏈結性**
- [ ] **Step 3: 模擬磁碟空間不足時的跨語言狀態解碼**

-e 

#2026-04-04 #gcs #plan #hardened #polish #integrity
✅ GCS Guardian v1.19 Fully Deployed and Sealed.
