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
    r"sk-[a-zA-Z0-9]{20,}",
    r"ghp_[a-zA-Z0-9]{36}",
    r"AIza[0-9A-Za-z\\-_]{35}",
        "notify_state": dot_gemini / "gcs_notify.state",
import json

# Advanced Secret Scrubbing patterns (Phase 2)
SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|token|secret|password|credential)",
    r"-----BEGIN .* PRIVATE KEY-----",
    r"sk-[a-zA-Z0-9]{20,}",
    r"ghp_[a-zA-Z0-9]{36}",
    r"AIza[0-9A-Za-z\\-_]{35}",
    r"xox[baprs]-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24}",
]

def load_project_config(project_root: str):
    """Load local overrides from .gemini/gcs_config.json if it exists."""
    global SECRET_PATTERNS
    config_file = os.path.join(project_root, ".gemini", "gcs_config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                cfg = json.load(f)
                if "SECRET_PATTERNS" in cfg:
                    SECRET_PATTERNS.extend(cfg["SECRET_PATTERNS"])
                    # Deduplicate
                    SECRET_PATTERNS = list(set(SECRET_PATTERNS))
        except Exception:
            pass

# Paths (derived from project root)
def get_paths(project_root: str) -> dict:
    load_project_config(project_root)
    root = Path(project_root)
    }

__version__ = "1.25.0"
