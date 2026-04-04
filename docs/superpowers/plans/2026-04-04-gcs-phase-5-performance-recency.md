# GCS Phase 5 - Performance Packing & Semantic Recency Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Small File Packing (SFP) to optimize bucket usage and Active Reference Counting (ARC) to enhance semantic fidelity for hot symbols.

**Architecture:** Distiller will now support packing multiple small skeletonized files into a single 4096-byte aligned "Common Bucket" instead of individual alignment. Orchestrator will track symbol access frequency to decide which function bodies to partially preserve.

---

### Task 1: Small File Packing (SFP) Engine
**Files:**
- Modify: `src/gcs/gcs_distiller.py`

- [ ] **Step 1: Implement `pack_skeletons()` to group small files (<1024 bytes)**
- [ ] **Step 2: Update `_apply_hysteresis` to only align large files or full-buckets**
- [ ] **Step 3: Modify `checkpoint.json` schema to support multi-file buckets**

### Task 2: Active Reference Counting (ARC)
**Files:**
- Modify: `src/gcs/lsp_bridge.py`
- Modify: `src/gcs/gcs_distiller.py`

- [ ] **Step 1: Implement symbol access tracking in `LSPBridge.query_definition`**
- [ ] **Step 2: Add `usage_count` metadata to skeletonized symbols**
- [ ] **Step 3: Preserve docstrings for symbols with `usage_count > 5` (Hot Symbols)**

### Task 3: Index Lock Awareness & Atomic Checkpoint
**Files:**
- Modify: `src/gcs/gcs_orchestrator.py`

- [ ] **Step 1: Implement `.git/index.lock` detection before starting distillation**
- [ ] **Step 2: Implement atomic JSON write (write to tmp -> rename) to prevent corruption**
- [ ] **Step 3: Final validation: Scan `gemini-cli` and verify 90%+ real token saving**
-e 

#2026-04-04
