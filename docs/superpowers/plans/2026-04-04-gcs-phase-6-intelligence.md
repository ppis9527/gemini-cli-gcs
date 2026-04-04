# GCS Phase 6 - Intelligence & Self-Healing Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Bucket Inline Manifest (BIM) for precise small file indexing, LFU Cache Eviction for memory safety, and Adaptive Fidelity (AF) for hot symbol preservation.

**Architecture:** Distiller will now embed a manifest at the top of each "Common Bucket". LSPBridge will manage L1 cache with LFU policy. Orchestrator will implement stale entry cleanup during the 20k trigger cycle.

---

### Task 1: Bucket Inline Manifest (BIM)
**Files:**
- Modify: `src/gcs/gcs_distiller.py`

- [ ] **Step 1: Update `pack_skeletons()` to prepend a compact Markdown index (Manifest)**
- [ ] **Step 2: Add `GCS_INDEX` tags for each file entry inside the bucket**
- [ ] **Step 3: Verify Agent's ability to locate files within packed buckets**

### Task 2: LFU Cache Eviction & Adaptive Fidelity (AF)
**Files:**
- Modify: `src/gcs/lsp_bridge.py`
- Modify: `src/gcs/gcs_distiller.py`

- [ ] **Step 1: Implement Least Frequently Used (LFU) eviction in `LSPBridge.l1_cache`**
- [ ] **Step 2: Implement `Adaptive Fidelity`: Preserve full Docstrings + first 3 lines of body for `[HOT_SYMBOL]`**
- [ ] **Step 3: Add `partial_preserve` flag to `_find_blocks_to_skeletonize`**

### Task 3: Self-Healing Orchestration
**Files:**
- Modify: `src/gcs/gcs_orchestrator.py`

- [ ] **Step 1: Implement `cleanup_stale_entries()`: Remove skeletons for files no longer in `git ls-files`**
- [ ] **Step 2: Add "Token Bidding" logic: Allow manual `/gcs:fidelity high` to override distillation for a session**
- [ ] **Step 3: Final E2E: Distill Large Repo -> Verify Manifest -> Verify Hot Symbol Body Preservation -> Verify Cleanup**
-e 

#2026-04-04
