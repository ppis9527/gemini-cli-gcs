# X-Tracker v3.4 Active Polling Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將 X-Tracker 從不穩定的 Nitter RSS 監控轉向基於 Playwright CDP 的「主動輪詢」(Active Polling)。

**Architecture:** 採用「解耦調度模式」(Modular Trigger)。`monitor_active.py` 作為計時調度器，每 15 分鐘透過 `subprocess` 調用重構後的 `scraper_playwright.py` 執行單次抓取任務。

**Tech Stack:** Python, Playwright (CDP), SQLite, Discord Webhook.

---

## Chunk 1: Scraper Refactoring & Robustness (Hardened)

**Files:**
- Modify: `scraper_playwright.py`
- Test: `tests/test_scraper_v34.py`

- [ ] **Step 1: 重構 Scraper 並加入隱身與資源攔截**
    - 實作 `intercept_route` 攔截 `png,jpg,jpeg,mp4,woff,woff2,otf,ttf`，保留 CSS。
    - **新增 (Stealth)**: 實作隨機模擬人類行為（隨機滾動、隨機停頓 1-3 秒）。
    - 實作 `data-testid="tweet"` 抓取，若抓取數為 0 則回報 `status: "potential_structure_change"` 並 `sys.exit(2)`。

- [ ] **Step 2: 實作結構化輸出與訊號處理**
    - 使用 `json.dumps` 輸出狀態。
    - **新增 (Cleanup)**: 實作 `signal.SIGTERM` 處理器，確保被 Monitor 強制停止時能正確關閉 Browser Context。

- [ ] **Step 3: 驗證單次抓取與資源攔截**
    - 執行 `python scraper_playwright.py` 並檢查 `tweets.db` 是否正確更新。

---

## Chunk 2: Active Monitor & Industrial Grade Resilience

**Files:**
- Create: `monitor_active.py`
- Create: `monitor_active.log`
- Create: `scripts/restart_chrome.sh` (新增: 層級式恢復腳本)
- Modify: `utils.py` (加入進程鎖、指標統計與日誌工具)

- [ ] **Step 1: 在 `utils.py` 加入 PID 驗證鎖、指標統計與日誌輪替**
    - **鎖機制**: 支援檢查 PID 存活 (`os.kill(pid, 0)`)，且若 PID 存在但啟動超過 20 分鐘（超時），則判定為殭屍進程並強制 `kill -9`。
    - **指標統計**: 實作簡單的 `metrics_collector` 紀錄成功/失敗次數與耗時。
    - **日誌機制**: 使用 `logging.handlers.RotatingFileHandler` (max 5MB, backupCount=3)。

- [ ] **Step 2: 實作 `monitor_active.py` 強化型循環與自我修復**
    - **新增 (Jitter)**: `time.sleep(900 + random.randint(-120, 120))` 防止固定間隔偵測。
    - **新增 (Venv Safety)**: 使用 `sys.executable` 調用 Scraper。
    - **新增 (Self-Healing)**: 若連續 3 次 CDP 連線失敗，自動調用 `scripts/restart_chrome.sh` 嘗試重啟瀏覽器。
    - **新增 (Heartbeat)**: 每 100 次循環或每日固定時間發送「指標化健康報告」（含成功率、平均耗時）至 Discord。支援 `DEBUG_HEARTBEAT=1` 立即觸發。

- [ ] **Step 3: 整合測試、破壞性驗證與部署**
    - **破壞性驗證**: 手動建立過期 PID 鎖檔案，驗證 Monitor 是否能正確執行 `kill -9` 並重啟任務。
    - 啟動 `nohup python monitor_active.py &`。
    - 驗證 `monitor_active.log` 是否正確執行輪替。

---
*Plan finalized on 2026-03-31. Self-Healing, Metrics, and Destructive Testing added.*
