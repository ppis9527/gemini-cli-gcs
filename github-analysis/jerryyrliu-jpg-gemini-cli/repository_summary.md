這個 GitHub 儲存庫 `jerryyrliu-jpg/gemini-cli` 是一個為 Gemini CLI 增強功能的技能集合。它目前包含一個名為「Gemini Memory Manager」的技能。

**主要目的：**
透過將冗長的對話日誌壓縮成簡潔的 Markdown 摘要，並儲存在每個專案資料夾中的 `GEMINI.md` 檔案中，來提供智慧型、專案特定的記憶體管理。

**主要功能：**
*   自動預載 `GEMINI.md` 檔案。
*   在接近上下文限制時（75%）建議進行快照，以主動管理 token 使用。

**技術要求：**
*   安裝 Node.js。
*   安裝此技能需要將 `gemini-memory-manager` 資料夾複製到 Gemini CLI 的技能目錄中。
-e 

#2026-04-04
