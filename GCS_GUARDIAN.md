# 🛰️ GCS Guardian: Context Governance System (SSOT)

> [!important] GCS Operation Guide (v1.26.0)
> This project is the GCS Guardian context governance system. All context and dialogue progress are protected by the L4 skeleton rehydration protocol, strictly executing 20% threshold distillation monitoring.

---

## 🏗️ System Mandates

### Project Isolation & Memory Protection Protocol (v3.0)
- **Project Isolation**: Context and memory are strictly restricted to their respective directories; automatic cross-directory aggregation is prohibited.
- **Manual Archiving**: Execute project-specific snapshots only upon explicit user command.
- **Vector Indexing**: `index_sync` performs incremental indexing only on raw source files.

---

## 🛰️ GCS (Context Governance System) Layered Architecture

All prompts and internal states must adhere to the following 6-layer layout to ensure prefix invariance and maximize KV Cache efficiency.

<gcs_layout_mandate>
1. [SYSTEM_MANDATES]: Core rules, security guidelines, and GCS operating specifications.
2. [SKILLS_KNOWLEDGE]: Activated agent skills and tool definitions.
3. [PROJECT_MANIFEST]: Project directory tree and environment variables within a 2k budget.
4. [CHECKPOINT_SUMMARY]: Skeletonized code injected by gcs_init.sh from .gemini/checkpoint.json.
5. [ACTIVE_SOURCE]: Complete content of files currently involved (aligned to 4096B buckets).
6. [EPHEMERAL_CONTEXT]: Real-time Git Diff, recent 3-turn dialogue history, and temporary tool outputs.
</gcs_layout_mandate>

## 📊 Governance Metrics & Thresholds (Context Governance Mandate)

### ♻️ GCS Lifecycle Flow (20% Threshold)
1. **Detection**: When `token_monitor.js` detects context usage reaching **20%**, it automatically triggers background distillation. The actual threshold is dynamically converted based on the model's context window, e.g., ~200k for 1M models, ~400k for 2M models.
2. **Alert**: When saturation reaches 80%, a terminal banner notification prompts the user to execute `/clear`.
3. **Resume**: After the user enters `/clear`, `gcs_init.sh` reads `checkpoint.json` to rehydrate the L4 skeleton and resume the task state.

---

## 📝 Markdown Tag Specifications
- All Markdown (.md) files must include a hashtag with the current date (#yyyy-mm-dd).
- All Markdown (.md) files must include relevant topic hashtags (e.g., #gcs #architecture).

---
*Updated to v1.26.0. GCS Guardian Ultimate SSOT.*

#gcs #architecture #ssot #2026-06-06
