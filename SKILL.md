---
name: custom-session-manager
description: Used for Autonomous Context Governance, Session Compaction (via /snapshot), and Long-term Memory Sync. V6.4.0 integrates rigorous Python bootstrap hooks, GCS Guardian, and ChromaDB vector synchronization across all platforms.
---

# Skill: Custom Session Manager (V6.3.0 Universal Hybrid)

## 🛰️ Module D: Autonomous Context Governance (GCS Guardian)
**Goal: No-ops Governance. Combat "Context Decay" via real-time monitoring and background distillation.**

### Execution Logic:
- **Rigorous Bootstrap Engine**: `SessionStart` and `AfterModel` hooks are explicitly routed via `python3 lib/bootstrap.py` for bulletproof multi-platform compatibility across Windows, gMac, and gLinux.
- **Real-time Monitoring**: Polled via Node.js subprocess to evaluate `usageMetadata` (skipping 0-token chunks) and display live status in Tmux (`[GCS: XX%]`).
- **Tiered Incremental Distillation**: When context reaches 20%, 30%, 40%, 50%, 60%, or 70%, the system automatically triggers `gcs_orchestrator.py` in the background with atomic watermark tracking to trim AST skeletons continuously.
- **80% Threshold (Critical Alert)**: Displays a banner alert asking the user to execute `/snapshot` or `/clear` to reset the session.

## 🧠 Module A: Tactical Compaction & Handoff (Command: /snapshot)
**Goal: Tactical Relay. Leverage GCS for high-fidelity skeletonization and Zlib-compressed checkpoints.**

### Execution Steps:
1. **Trigger Distillation**: Call `lib/gcs_adapter.py` to perform a full distillation of active/tracked files.
2. **Generate 6-Layer Handoff**:
   - **L1 (Mandates)**: Core security and GCS protocols.
   - **L2 (Skills)**: Activated agent skills and tool definitions.
   - **L3 (Manifest)**: Project directory tree.
   - **L4 (GCS Skeletons)**: Inject content from `.gemini/checkpoint.json`.
   - **L5 (Active Source)**: Preserve critical files currently being edited.
   - **L6 (Ephemeral)**: Recent history, Git Diffs, and Pending Tasks.
3. **Archiving**: Save a copy to `"[gdrive]/Gemini CLI/Snapshots/Snapshot-yyyy-mm-dd-[topic].md"`.

## 🗄️ Module C: Long-term Memory Sync (Command: /scan2db)
**Goal: Global Memory Alignment. Synchronize Obsidian Vault with the vector database.**

### Execution Pipeline:
1. `step1_scan.py` -> 2. `step2_embed.py` -> 3. `build_bm25.py`.
(Scripts located in "[gdrive]/Gemini_Memory_System_Package/mcp_server/")

## 🚀 Command Summary
- **/snapshot**: Triggers high-fidelity distillation and guides session restart.
- **/scan2db**: Syncs local notes to long-term memory (ChromaDB).
- **GCS Status**: Check Tmux status bar or `.gemini/gcs.log` for real-time governance stats.

#custom-session-manager #gcs #guardian #universal #hybrid #2026-06-05
