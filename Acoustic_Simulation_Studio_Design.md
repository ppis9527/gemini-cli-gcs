# Acoustic Simulation Studio 設計文件 (SSOT)

> **版本**: 1.7
> **狀態**: Task 11 (UI 重構 & 品質門戶) 完成 ✅
> **目標**: 建立一個基於專業 Agent 分工的聲學體素模擬開發環境。
> **上次更新**: 2026-03-29

## 1. 系統架構 (System Architecture)

### 1.1 系統架構圖 (Architecture Diagram)
(保留原有 Mermaid 圖表...)

### 1.2 Agent 層級與職責
(保留原有職責描述...)

### 1.3 互動協議 (Protocols)
- **Agent 品質門戶 (Quality Gate)**: 模擬前由 Physicist 自動檢查 BC 與解析度，未通過則警告。

### 1.4 UI 架構 (Option 1: Functional-oriented)
- **`web_app.py`**: 主入口，負責 Session 初始化與路由。
- **`views/geometry_view.py`**: CAD/Voxel 配置。
- **`views/solver_view.py`**: 求解器配置、Agent 審核與實時繪圖。
- **`views/results_view.py`**: 後處理分析與下載。

---

## 9. 實時反饋與品質門戶 (Real-time Feedback & Quality Gate)

### 9.1 Agent 預檢 (Pre-check)
- **邏輯**: 調用 `/check-bc` 與 `/audit-sim`。
- **UI 行為**: 側邊欄顯示 🟢/🔴/🟡 審查意見。

### 9.2 實時繪圖 (Live Plotting)
- **數據流**: `LEMSolver.compute_frequency_response_generator` -> `st.plotly_chart`。
- **優點**: 每 5 個頻點更新一次曲線，提升心理舒適度。

---
*Last updated 2026-03-29 — UI 重構與 Agent 門戶實作完成。*
-e 

#2026-04-04
