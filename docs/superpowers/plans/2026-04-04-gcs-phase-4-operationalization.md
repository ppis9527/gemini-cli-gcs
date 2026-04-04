# GCS Phase 4 - Operationalization & Full-Repo Health Report

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automate GCS distillation based on token pressure and generate a comprehensive "Context Health Report" for the entire `gemini-cli` repository.

**Architecture:** A lightweight background monitor (`gcs_monitor.py`) that tracks session tokens and triggers `gcs_distiller.py`. A reporting tool (`gcs_health_report.py`) that aggregates `sst_bench.py` results.

---

### Task 1: Full-Repo Context Health Report
**Files:**
- Create: `src/gcs/gcs_health_report.py`

- [ ] **Step 1: Implement `git ls-files` based repository scanner in `gcs_health_report.py` (Fast & Respect .gitignore)**
- [ ] **Step 2: Aggregate `sst_bench.py` metrics (Original vs Distilled vs Aligned)**
- [ ] **Step 3: Generate Markdown report with "Token Saving Potential"**
- [ ] **Step 4: Run report on `gemini-cli` and save to `docs/gcs/health_report_2026-04-04.md`**

### Task 2: Auto-Distillation Orchestrator & Safety
**Files:**
- Create: `src/gcs/gcs_orchestrator.py`

- [ ] **Step 1: Implement File Lock (`.gemini/gcs.lock`) to prevent race conditions during auto-distill**
- [ ] **Step 2: Implement Token-Aware trigger logic (threshold = 20k)**
- [ ] **Step 3: Integrate `gcs_distiller.py` and embed `git rev-parse HEAD` into `checkpoint.json`**
- [ ] **Step 4: Implement background execution with logging to `.gemini/gcs.log`**

### Task 3: Shell & Branch-Aware Integration
**Files:**
- Modify: `src/gcs/gcs_init.sh`
- Modify: `GEMINI.md` (Update Operational Mandates)

- [ ] **Step 1: Enhance `gcs_init.sh` to verify `commit_sha` before restoration (Prevent Branch Poisoning)**
- [ ] **Step 2: Add GCS activation instructions to the project's README/GEMINI.md**
- [ ] **Step 3: Final End-to-End test: Switch branch -> Verify Reset -> Trigger 20k -> Verify Auto-Checkpoint**
