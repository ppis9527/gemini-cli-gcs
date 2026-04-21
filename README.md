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

For deep technical details, see [GCS_GUARDIAN.md](./GCS_GUARDIAN.md) and the [Technical Whitepaper](./docs/GCS-Guardian-Ultimate-Whitepaper-v1.20.md).

---
*Created by Gemini 3.1 Pro. v1.21 Refined 2026-04-08.*
#gcs #governance #architecture #gemini-cli

## 📈 Change List

### [2026-04-21] Universal Supply Chain Intelligence (USCI) Framework
- **Universal Upgrade**: Transitioned from CPO-specific tracking to a generalized industrial intelligence framework.
- **Semantic Search Architecture**: Adopted  for ACID-compliant vector search, unified at 768 dimensions (Nomic/Google API aligned).
- **Two-Stage Filtering**: Implemented a robust extraction pipeline: Vector Recall (Stage 1) -> LLM Reasoning (Stage 2).
- **Entity Resolution 2.0**: Added Wikidata integration for automated ticker and industry alignment.
- **Schema Generalization**: Renamed core tables to  and  with multi-industry context support.
