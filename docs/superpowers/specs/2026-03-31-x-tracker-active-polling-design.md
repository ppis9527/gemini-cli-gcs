# X-Tracker v3.4 Active Polling 設計規格書

## 1. 目的
解決 Nitter RSS 不穩定導致的監控失效。將系統從「被動接收」改為「主動輪詢」，利用現有的 CDP (Chrome DevTools Protocol) 連線確保抓取穩定性。

## 2. 系統架構 (方案 B：解耦調度模式)

### 2.1 組件設計
1. **`monitor_active.py` (調度器)**:
   - 每 15 分鐘執行一次。
   - 負責日誌記錄 (`monitor_active.log`)。
   - 使用 `subprocess` 調用 `scraper_playwright.py`。
2. **`scraper_playwright.py` (執行器)**:
   - 優化 CDP 連線 (127.0.0.1:9222)。
   - 支援參數化單帳號掃描。
   - 自動將新推文寫入 SQLite 並推送 Discord。

### 2.2 資料流
`monitor_active.py` -> `scraper_playwright.py` -> `X.com (via CDP)` -> `tweets.db` -> `Discord Webhook`

## 3. 核心邏輯演進
- **連線檢查**: Scraper 啟動時先檢查 9222 埠是否可用。
- **去重機制**: 依賴 SQLite `INSERT OR IGNORE` 與 Twitter 唯一 ID。
- **錯誤恢復**: 若 Scraper 執行失敗，Monitor 會紀錄錯誤並在下一個循環重試，不會導致系統掛起。

## 4. 驗證標準
- [ ] `monitor_active.py` 能穩定在後台執行。
- [ ] 每 15 分鐘觸發一次掃描。
- [ ] 模擬 CDP 離線時，Monitor 需有正確的錯誤紀錄而非崩潰。
