# ADR 0003: 實作雙重 Context 壓縮防線 (50% vs. 60%)
**日期**: 2026-02-26
**狀態**: 已通過 (Accepted)

## 上下文 (Context)
Gemini CLI 預設的自動壓縮 (Auto-Compression) 可能會在我們完成高品質專案存檔 (Senior Save) 之前就清空對話歷史。

## 決策 (Decision)
1. **官方門檻上調**: 將全域 `settings.json` 的 `autoCompressionThreshold` 設定為 **0.6 (60%)**。
2. **技能門檻下修**: 將 `gemini-session-manager` 的智慧存檔門檻設定為 **0.5 (50%)**。

## 理由 (Rationale)
- **10% 黃金緩衝區**: 提供足夠的 Token 空間讓 LLM 進行深度摘要與 ADR 盤點。
- **防止記憶遺失**: 確保在官方執行「強制壓縮」之前，我們已經完成了 `GEMINI.md` 的更新與 GitHub 同步。

## 後果 (Consequences)
- 優點: 記憶連續性更高，存檔流程更穩定。
- 缺點: 如果頻繁在 50%-60% 區間對話，會收到較多存檔提示。
-e 

#2026-04-04
