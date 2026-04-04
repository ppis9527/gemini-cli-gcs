# GCS Phase 3 - LSP Bridge & Semantic Perception Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a multi-tier LSP bridge and integrate it with GCS Distiller to enhance skeletonization with semantic awareness (definitions, types, and cross-references).

**Architecture:** A standalone Python bridge communicating with language servers (via LSP) providing three-tier response logic: L1 (Fast Cache), L2 (LSP Request with 200ms timeout), and L3 (Asynchronous fallback/Skeleton-only).

**Tech Stack:** Python, `pylsp` (Python), `typescript-language-server` (JS/TS), `jsonrpc`.

---

### Task 1: Environment & LSP Scaffolding
**Files:**
- Create: `src/gcs/lsp_bridge.py`
- Create: `tests/gcs/test_lsp_bridge.py`

- [x] **Step 1: Write setup test for LSP Bridge**
- [x] **Step 2: Implement basic JSON-RPC client for LSP**
- [x] **Step 3: Implement multi-tier timeout logic (L1/L2/L3)**

### Task 2: Python LSP Integration (L1/L2)
**Files:**
- Modify: `src/gcs/lsp_bridge.py`
- Modify: `tests/gcs/test_lsp_bridge.py`

- [x] **Step 1: Implement `initialize` and `textDocument/definition` for Python**
- [x] **Step 2: Verify 200ms timeout L2 logic**
- [x] **Step 3: Implement L1 local cache for frequent symbols**

### Task 3: JS/TS LSP Integration
**Files:**
- Modify: `src/gcs/lsp_bridge.py`

- [x] **Step 1: Add support for `typescript-language-server`**
- [x] **Step 2: Verify cross-file definition lookup**

### Task 4: Semantic Distiller Integration
**Files:**
- Modify: `src/gcs/gcs_distiller.py`
- Modify: `src/gcs/lsp_bridge.py`

- [x] **Step 1: Enhance `_find_blocks_to_skeletonize` to use LSP for "hot" symbol resolution**
- [x] **Step 2: Preserve type signatures and docstrings based on LSP metadata**

### Task 5: End-to-End Validation & Benchmarking
**Files:**
- Modify: `src/gcs/sst_bench.py`

- [x] **Step 1: Add "Semantic Fidelity" metric to `sst_bench.py`**
- [x] **Step 2: Compare Skeleton-only vs Semantic-aware distillation on large codebase**
-e 

#2026-04-04
