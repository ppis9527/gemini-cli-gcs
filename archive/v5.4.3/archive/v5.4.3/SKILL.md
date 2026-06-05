---
name: custom-session-manager
description: Used for Session Compaction, Project Snapshots, and Long-term Memory Sync. V5.4.3 supports High-Fidelity Skeletonization and 6-Layer Context Governance.
---

# Skill: Custom Session Manager (V5.4.3 3.1 Pro Standard)

## 🚨 Resource Safety Check (Pre-flight Check)
- **Memory Threshold Check**: Check system available memory before starting large tasks.
- **Logic**: If available memory < 20%, stop and notify the user to close high-usage programs.

## 🧠 Module A: Tactical Compaction & Handoff (Command: /compact)
Execute when Tokens > 200,000 or conversation exceeds 20 turns.
**Goal: Tactical Relay. Restart the CLI to release physical memory and ensure the new Agent starts quickly via "Segmented Injection".**

### Execution Steps:
1. **Generate Segmented Summary**:
   - **L1-L3 (Static Layers)**: Preserve core mandates and project manifest.
   - **L4 (Handoff Skeleton Core)**:
     - **Session Stats**: Tool usage frequency and success rate.
     - **North Star Goal**: Extract the primary objective from recent messages and place it at the top.
     - **Code Skeletons**: Run `python3 "[gdrive]/Skills_MCP_Extension/skills-source/unix-shared/custom-session-manager/lib/skeletonize.py" [path]` on the **Top 5 most recently accessed files**.
   - **L5 (Active Source Buffer)**: Preserve critical code snippets, subject to token Quota.
   - **L6 (Ephemeral Context)**: Recent conversation timeline, Git Diffs, and Pending Tasks.
2. **Archiving**: Use `write_file` to save to `"[gdrive]/Gemini CLI/Snapshots/Compact-yyyy-mm-dd-[topic].md"`.
3. **Handover Instructions**: Output the following format:
   > "✅ **Context Compression Complete!** File saved to: `"[Path]"`
   > 
   > ⚠️ **Please perform the following steps to release memory and continue seamlessly:**
   > 1. Press `Ctrl+C` to exit the current CLI.
   > 2. Restart `gemini`.
   > 3. **Paste and execute this command in the new session:**
   >    `Please immediately call the read_file tool to read "[File Path]". Strictly follow the L1-L6 layout to understand the state. If skeletons mismatch physical code, prioritize physical code. Current Task: [Task Description].`"

## 📜 Module B: Strategic Project Snapshot (Command: /snapshot)
**Goal: Strategic Recording. Track project evolution and architectural decisions over the long term.**

### Execution Steps:
1. **Generate Deep Archive**: Include Goal, Progress (with evidence), ADR (Architectural Decision Records), Constraints, and Git State.
2. **Archiving**: Save to `"[gdrive]/Gemini CLI/Snapshots/Snapshot-yyyy-mm-dd-[topic].md"`.

## 🗄️ Module C: Long-term Memory Sync (Command: /scan2db)
**Goal: Persistence Reset. Synchronize Obsidian Vault with the vector database.**

### Execution Pipeline:
1. `step1_scan.py` -> 2. `step2_embed.py` -> 3. `build_bm25.py`.
(Scripts located in "[gdrive]/Gemini_Memory_System_Package/mcp_server/")

## 🚀 Command Summary
- **/compact**: Triggers Module A. Performs high-fidelity compaction and guides the restart.
- **/snapshot**: Triggers Module B. Backs up overall progress and architectural records.
- **/scan2db**: Triggers Module C. Syncs local notes to long-term memory (ChromaDB).

#2026-05-13
