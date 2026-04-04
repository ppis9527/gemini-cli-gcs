# GCS Phase 7 - Dynamic Re-hydration & Automated Closed-Loop Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable seamless editing of skeletonized code by implementing AST Source Mapping and automated block re-hydration.

**Architecture:**
1. **Source Mapping**: Upgrade `checkpoint.json` to store function metadata (original start/end bytes).
2. **Interception Hook**: Implement a middleware that detects when an Agent's `replace` call targets a skeletonized line.
3. **Ghost Replacement**: Automatically swap the skeletonized block with original code before the Agent's tool execution.

---

### Task 1: AST Source Mapping (Metadata Upgrade)
**Files:**
- Modify: `src/gcs/gcs_distiller.py`
- Modify: `src/gcs/gcs_orchestrator.py`

- [ ] **Step 1: Update `_find_blocks_to_skeletonize` to record `(symbol_name, start_byte, end_byte, distilled_placeholder)`**
- [ ] **Step 2: Modify `GCSDistiller.skeletonize` to return a `source_map` object**
- [ ] **Step 3: Update `GCSOrchestrator` to persist the `source_map` in `checkpoint.json`**

### Task 2: Re-hydration Discovery Engine
**Files:**
- Create: `src/gcs/gcs_rehydrator.py`

- [ ] **Step 1: Implement `find_original_block(file_path, line_number)` logic using Source Map**
- [ ] **Step 2: Implement `get_full_context(file_path, symbol_name)` to fetch original code from disk**
- [ ] **Step 3: Verify mapping accuracy between skeletonized lines and original byte ranges**

### Task 3: Tool-Level Interception (The "No-Op" Bridge)
**Files:**
- Create: `src/gcs/gcs_intercept.py`
- Modify: `src/gcs/gcs_init.sh`

- [ ] **Step 1: Implement an interception script that checks if a target file is "Skeletonized"**
- [ ] **Step 2: Implement "Just-in-Time Re-hydration": Automatically restore the specific file before any `replace` or `read_file` tool call**
- [ ] **Step 3: Final E2E: Distill File -> Agent tries to edit Distilled Function -> System Restores File -> Edit Succeeds without NameError**
-e 

#2026-04-04
