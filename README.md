# Gemini CLI Context Governance System (GCS Guardian)

GCS Guardian is an industrial-grade self-regulating framework for Gemini CLI, designed to combat "Context Decay" in long-running development sessions.

## 🚀 Key Features

- **AST Skeletonization**: Compresses large source code files into high-fidelity skeletons using Tree-sitter, reducing token usage by >90% while maintaining semantic structure.
- **Prefix-Invariant Layering**: Optimized for maximum KV Cache hit ratios by enforcing a strict 6-layer prompt layout.
- **Zlib Compression (v1.21)**: Checkpoints are compressed using RFC 1950 (Zlib) and Base64 encoded to keep context overhead <4KB.
- **Atomic Concurrency Protection**: Implements cross-process atomic file locking using `fcntl` (Python) and exclusive `wx` creation (Node.js) to prevent race conditions during background distillation.
- **Thread-Safe Singletons**: Robust rehydration mechanism with thread-safe initialization.
- **LSP Integration**: Semantic awareness via Language Server Protocol (LSP) to automatically preserve implementations of "Hot Symbols".

## 🛠️ Components

- `gcs_distiller.py`: The "brain" responsible for AST parsing and skeletonization.
- `gcs_orchestrator.py`: Manages the lifecycle of distillation, checkpoints, and task states.
- `lsp_bridge.py`: High-performance asynchronous bridge to `pylsp` with LFU caching.
- `token_monitor.js`: Proactive hook for real-time token usage monitoring and background trigger.
- `gcs_rehydrator.py`: Efficient logic for restoring original code blocks from skeletons.

## 📦 Installation

This system is designed to be installed as a Gemini CLI Global Extension.

1. Clone the repository.
2. Run `src/gcs/setup.sh` to initialize the virtual environment.
3. Register the hooks in your `~/.gemini/settings.json`.

## 📜 Specification

For deep technical details, see [GCS_GUARDIAN.md](./GCS_GUARDIAN.md) and the [Technical Whitepaper](./docs/gcs/GCS-Guardian-Ultimate-Whitepaper-v1.22.0.md).

---
*Created by Gemini 3.1 Pro. v1.23.0 Refined 2026-05-24.*
#gcs #governance #architecture #gemini-cli

## 📈 Change List

### [2026-05-24] GCS Guardian v1.23.0: YOLO Double-Threshold & Session Boundary Refinements
- **Double-Threshold YOLO**: Context at 20% triggers quiet background `summarize` (AST skeletons checkpointed to `checkpoint.json` & `.gemini/gcs.pending` as `status: Summarized`), displaying `xx.x% ⚡` in footer and tmux without clearing the active Session history. Standard `Governance Triggered` status and Cold Reset (clearing history) are deferred until 60% system-level Compaction or manual `/compress`.
- **UI Format Refinements**: Standardized all GCS context usage percentages to display with exactly 1 decimal place (e.g. `xx.x% ⚡`) across statusline and tmux status files.
- **Verbose Log Silencing**: Completely removed the 5% verbose incremental console logger (`📊 [GCS]`) from `token_monitor.js` to avoid cluttering tool outputs.

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
