# Gemini CLI Context Governance System (GCS Guardian)

GCS Guardian is an industrial-grade self-regulating framework for Gemini CLI, designed to combat "Context Decay" in long-running development sessions.

## 🚀 Key Features

- **AST Skeletonization**: Compresses large source code files into high-fidelity skeletons using Tree-sitter, reducing token usage by >90% while maintaining semantic structure.
- **Preflight Dependency Guard**: `gcs_preflight.py` validates required parser dependencies before background compaction starts.
- **Prefix-Invariant Layering**: Optimized for maximum KV Cache hit ratios by enforcing a strict 6-layer prompt layout.
- **Zlib Compression (v1.21)**: Checkpoints are compressed using RFC 1950 (Zlib) and Base64 encoded to keep context overhead <4KB.
- **Atomic Concurrency Protection**: Implements cross-process atomic file locking using `fcntl` (Python) and exclusive `wx` creation (Node.js) to prevent race conditions during background distillation.
- **Thread-Safe Singletons**: Robust rehydration mechanism with thread-safe initialization.
- **LSP Integration**: Semantic awareness via Language Server Protocol (LSP) to automatically preserve implementations of "Hot Symbols".
- **Multi-Threshold Background Compact**: Automatically runs background compaction at 20%, 30%, 40%, and 50% context usage with per-threshold deduplication.

## 🛠️ Components

- `gcs_distiller.py`: The "brain" responsible for AST parsing and skeletonization.
- `gcs_orchestrator.py`: Manages the lifecycle of distillation, checkpoints, and task states.
- `lsp_bridge.py`: High-performance asynchronous bridge to `pylsp` with LFU caching.
- `token_monitor.js`: Proactive hook for real-time token usage monitoring and background trigger.
- `gcs_rehydrator.py`: Efficient logic for restoring original code blocks from skeletons.
- `gcs_preflight.py`: Runtime dependency checker used by `token_monitor.js`.

## 📦 Installation

This system is designed to be installed as a Gemini CLI Global Extension.

1. Clone the repository.
2. Create project-local virtualenv: `python3 -m venv .gemini/gcs-venv`.
3. Install dependencies into that virtualenv: `.gemini/gcs-venv/bin/python3 -m pip install -r requirements.txt`.
4. (Optional) run preflight check: `.gemini/gcs-venv/bin/python3 src/gcs/gcs_preflight.py`.
5. Register the hooks in your `~/.gemini/settings.json`.
6. Configure tmux to read the session-aware status script:
   ```tmux
   set -g status-right "#($HOME/.gemini/extensions/gcs-guardian/scripts/tmux_status.sh '#{session_id}')"
   ```
   If you already have a longer `status-right`, append the script to your existing chain and keep `status-interval` enabled.

## 🧪 Quick Test

1. Run JS monitor tests: `node tests/test_token_monitor.js`
2. Run Python syntax check: `python3 -m py_compile src/gcs/*.py`

## ⚙️ Runtime Behavior

- Token source: `usageMetadata.promptTokenCount` (Gemini) or `usage.input_tokens` (Claude/OpenAI-compatible shape).
- Model context mapping (current defaults):
  - `gemini-2.5-pro` -> `2097152`
  - `gemini-2.5-flash` -> `1048576`
  - unknown model -> fallback `1048576`
- Background compact thresholds: `20%`, `30%`, `40%`, `50%`
- Catch-up behavior: if usage jumps across multiple thresholds in one step, all missed thresholds are triggered in order.

## 📜 Specification

For deep technical details, see [GCS_GUARDIAN.md](./GCS_GUARDIAN.md) and the [Technical Whitepaper](./docs/gcs/GCS-Guardian-Ultimate-Whitepaper-v1.22.0.md).

---
*Created by Gemini 3.1 Pro. v1.25.0 Session-Aware 2026-06-01.*
#gcs #governance #architecture #gemini-cli

## 📈 Change List

### [2026-06-01] GCS Guardian v1.25.0: Session-Aware Tmux Status and Token Isolation
- Made `token_monitor.js` session-aware by keying runtime state off tmux `session_id`, so prompt history and trigger buckets no longer bleed across sessions.
- Added `tmux_status.sh` and updated tmux setup so `status-right` automatically follows the active tmux session.
- Updated the installation guide and runtime docs to reflect the new session-scoped status files.
- Added regression coverage for session-reset behavior and runtime path generation.

### [2026-05-31] GCS Guardian v1.24.0: Reliability & Multi-Threshold Compact
- Added `requirements.txt` and `gcs_preflight.py` for predictable runtime dependency checks.
- Refined `token_monitor.js` with explicit model-to-context mapping and non-silent error reporting.
- Upgraded compaction triggers from single-threshold behavior to ordered `20/30/40/50` threshold execution with deduplication.
- Fixed interceptor/runtime integration issues and added lightweight regression tests (`tests/test_token_monitor.js`, `tests/test_intercept.py`).

### [2026-05-24] GCS Guardian v1.23.0: YOLO Double-Threshold & Session Boundary Refinements
- **Double-Threshold YOLO**: Context at 20% triggers quiet background `summarize` (AST skeletons checkpointed to `checkpoint.json` & `.gemini/gcs.pending` as `status: Summarized`), displaying `xx.x% ⚡` in footer and tmux without clearing the active Session history. Standard `Governance Triggered` status and Cold Reset (clearing history) are deferred until 60% system-level Compaction or manual `/compress`.
- **UI Format Refinements**: Standardized all GCS context usage percentages to display with exactly 1 decimal place (e.g. `xx.x% ⚡`) across statusline and tmux status files.
- **Verbose Log Silencing**: Reduced noisy progress logs in the standard flow.

### [2026-05-18] GCS Guardian v1.22.0: Precision Monitoring & Tmux Integration
- **Cross-Model Compatibility**: Dynamically parses Gemini's `usageMetadata.promptTokenCount` and Claude/OpenAI's `usage.input_tokens` in `token_monitor.js`.
- **Tmux Integration**: Unconditional state reset to `[GCS: 0%]` via `gcs_init.sh` and real-time lightweight status polling via `tmux_status`. Visual banner alerts triggered on YOLO distillations via `tmux display-message`.
- **Global Hook Binding**: Deprecated `extension.json` binding for `AfterModel` due to CLI module loading restrictions, migrating to `~/.gemini/settings.json` with `matcher: "*"`.
- **Whitepaper Update**: Upgraded architectural SSOT to v1.22.0.

### [2026-04-21] Universal Supply Chain Intelligence (USCI) Framework
- **Universal Upgrade**: Transitioned from CPO-specific tracking to a generalized industrial intelligence framework.
- **Semantic Search Architecture**: Adopted  for ACID-compliant vector search, unified at 768 dimensions (Nomic/Google API aligned).
- **Two-Stage Filtering**: Implemented a robust extraction pipeline: Vector Recall (Stage 1) -> LLM Reasoning (Stage 2).
- **Entity Resolution 2.0**: Added Wikidata integration for automated ticker and industry alignment.
- **Schema Generalization**: Renamed core tables to  and  with multi-industry context support.
