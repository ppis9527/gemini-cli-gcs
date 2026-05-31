import subprocess
import sys
from pathlib import Path


def test_intercept_check_intent_runs():
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "src" / "gcs" / "gcs_intercept.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--check-intent"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "GCS_INTERCEPT" in proc.stdout or "RE-HYDRATION_REQUIRED" in proc.stdout
