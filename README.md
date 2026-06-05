# Custom Session Manager (GCS Guardian)

GCS Guardian is an industrial-grade self-regulating framework for Gemini CLI, designed to combat "Context Decay" in long-running development sessions.

## 🚀 Key Features

- **AST Skeletonization**: Compresses large source code files into high-fidelity skeletons using Tree-sitter, reducing token usage by >90% while maintaining semantic structure.
- **Preflight Dependency Guard**: `gcs_preflight.py` validates required parser dependencies before background compaction starts.
- **Prefix-Invariant Layering**: Optimized for maximum KV Cache hit ratios by enforcing a strict 6-layer prompt layout.
- **Zlib Compression (v1.21)**: Checkpoints are compressed using RFC 1950 (Zlib) and Base64 encoded to keep context overhead <4KB.
- **Atomic Concurrency Protection**: Implements cross-process atomic file locking using `fcntl` (Python) and exclusive `wx` creation (Node.js) to prevent race conditions during background distillation.
- **Thread-Safe Singletons**: Robust rehydration mechanism with thread-safe initialization.
- **LSP Integration**: Semantic awareness via Language Server Protocol (LSP) to automatically preserve implementations of "Hot Symbols".
- **Multi-Threshold Background Compact**: Automatically runs background compaction at 20%, 30%, 40%, 50%, 60%, and 70% context usage with per-threshold deduplication.

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
  - Gemini `pro` models -> `2097152`
  - Gemini non-`pro` models -> `1048576`
  - Claude `sonnet` / `opus` -> `200000`
  - `gpt-oss-120b` -> `131072`
  - unknown model -> fallback `1048576`
- Background compact thresholds: `20%`, `30%`, `40%`, `50%`, `60%`, `70%`
- Catch-up behavior: if usage jumps across multiple thresholds in one step, all missed thresholds are triggered in order.

## 📜 Specification

For deep technical details, see [GCS_GUARDIAN.md](./GCS_GUARDIAN.md) and the [Technical Whitepaper](./docs/gcs/GCS-Guardian-Ultimate-Whitepaper.md).

---
*Created by Gemini 3.1 Pro. Version 6.4.0 (GCS Guardian v1.26.0) 2026-06-06.*
#gcs #governance #architecture #gemini-cli

## 📈 Change Log

### V6.4.0 (2026-06-05)
- **Unified Snapshot Compaction**: Removed the original Strategic Project Snapshot module, retaining only the Tactical Compaction module, and changed the corresponding command from `/compact` to `/snapshot`.
- Cleaned up obsolete configuration files and deprecated CLI hooks.

### V6.3.0 (2026-06-04)
- **Session-Aware Tmux Status (v1.25.0)**: Made `token_monitor.js` session-aware by keying runtime state off tmux `session_id`, preventing prompt history bleeding across sessions.
- **Tiered Incremental Distillation (v1.24.0)**: Introduced `DISTILL_TIERS` to replace the single 20% threshold with progressive pruning at 20%, 30%, 40%, 50%, 60%, and 70%.
- Implemented atomic watermark recording (`gcs_watermark.json`) in `gcs_orchestrator.py` to prevent repeated threshold triggers.
- Added `requirements.txt` and `gcs_preflight.py` for predictable runtime dependency checks.
- Refined `token_monitor.js` with explicit model-to-context mapping and non-silent error reporting.

### V6.2.0 (2026-05-30)
- **Universal Hybrid**: Integrated explicit bootstrap architecture from Windows version, binding `python3 lib/bootstrap.py` in `gemini-extension.json`.
- Added defensive virtualenv recovery engine (`sys.executable`) and non-blocking safe stdin reading in `bootstrap.py`.
- Retained Module C (`/scan2db`) and real-time Tmux status updates.

### V6.0.1 (2026-05-21)
- Added 10k token cooldown mechanism in `token_monitor.js`.
- Fixed osascript shell escape syntax errors.
- Added formal Change Log section.

### V6.0.0 (2026-05-18)
- Integrated GCS Guardian automation framework.
- Supported background YOLO distillation and Tmux status display.

### V5.4.3 (2026-05-13)
- Introduced AST-level code skeletonization.
- Defined 6-layer context governance architecture.
