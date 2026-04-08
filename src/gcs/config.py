"""GCS Configuration — Single Source of Truth for all thresholds and paths."""
import os
from pathlib import Path

# Context Governance
CONTEXT_WINDOW = 2_000_000          # Gemini 2.5 Pro
THRESHOLD_RATIO = 0.20              # 20%
THRESHOLD_TOKENS = int(CONTEXT_WINDOW * THRESHOLD_RATIO)  # 400k
CRITICAL_RATIO = 0.80               # 80% → warn user

# Distiller
BUCKET_SIZE = 4096
BUCKET_SLACK = 64
SMALL_FILE_THRESHOLD = 1024         # bytes
HOT_SYMBOL_QUERY_THRESHOLD = 5
HOT_SYMBOL_PRESERVED_LINES = 10

# LSP
LSP_CACHE_MAX = 1000
LSP_EVICT_RATIO = 0.10
LSP_RESPONSE_TIMEOUT = 0.2         # seconds

# Circuit Breaker (Phase 2)
AST_NODE_LIMIT = 30_000
LEAN_MODE_FIDELITY = 0

# Secret Scrubbing patterns (Phase 2)
SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|token|secret|password|credential)",
    r"-----BEGIN .* PRIVATE KEY-----",
]

# Paths (derived from project root)
def get_paths(project_root: str) -> dict:
    root = Path(project_root)
    dot_gemini = root / ".gemini"
    return {
        "dot_gemini": dot_gemini,
        "checkpoint": dot_gemini / "checkpoint.json",
        "lock": dot_gemini / "gcs.lock",
        "log": dot_gemini / "gcs.log",
        "pending": dot_gemini / "gcs.pending",
        "notify_state": dot_gemini / "gcs_notify.state",
    }

__version__ = "1.21.0"
