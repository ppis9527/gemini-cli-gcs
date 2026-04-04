import os
import sys
import json
import time
import subprocess
import fcntl
from gcs_distiller import GCSDistiller

class GCSOrchestrator:
    def __init__(self, root_path, threshold=20000):
        self.root_path = root_path
        self.threshold = threshold
        self.dot_gemini = os.path.join(root_path, ".gemini")
        os.makedirs(self.dot_gemini, exist_ok=True)
        self.checkpoint_path = os.path.join(self.dot_gemini, "checkpoint.json")
        self.lock_path = os.path.join(self.dot_gemini, "gcs.lock")
        self.log_path = os.path.join(self.dot_gemini, "gcs.log")

    def _log(self, message):
        # Basic log rotation (keep last 1MB)
        try:
            if os.path.exists(self.log_path) and os.path.getsize(self.log_path) > 1024 * 1024:
                os.rename(self.log_path, self.log_path + ".old")
        except Exception:
            pass
        with open(self.log_path, "a") as f:
            f.write(f"[{time.ctime()}] {message}\n")

    def should_distill(self, current_tokens):
        return current_tokens >= self.threshold

    def run_distillation(self, active_files):
        # Prevent race conditions with file lock
        try:
            lock_f = open(self.lock_path, "w")
            fcntl.flock(lock_f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError, OSError):
            self._log("Distillation already in progress, skipping.")
            return False

        try:
            self._log(f"Starting auto-distillation for {len(active_files)} files.")
            start_time = time.perf_counter()
            
            distiller = GCSDistiller()
            skeletons = {}
            for f_path in active_files:
                if os.path.exists(f_path):
                    with open(f_path, "r") as f:
                        content = f.read()
                    skeletons[f_path] = distiller.skeletonize(f_path, content)

            # Get current Git SHA
            try:
                commit_sha = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], 
                    cwd=self.root_path, 
                    text=True
                ).strip()
            except Exception:
                commit_sha = "no-git-repo"

            # Write Checkpoint
            checkpoint = {
                "gcs_version": "1.7",
                "timestamp": time.time(),
                "commit_sha": commit_sha,
                "project_root": self.root_path,
                "skeletons": skeletons
            }
            
            os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
            with open(self.checkpoint_path, "w") as f:
                json.dump(checkpoint, f, indent=2)

            duration = (time.perf_counter() - start_time) * 1000
            self._log(f"Distillation complete in {duration:.2f}ms.")
            return True
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)
            lock_f.close()

if __name__ == "__main__":
    # Example usage via CLI
    if len(sys.argv) > 1:
        tokens = int(sys.argv[1])
        orchestrator = GCSOrchestrator(os.getcwd())
        if orchestrator.should_distill(tokens):
            # Simulation of active files promotion
            orchestrator.run_distillation(["src/gcs/gcs_distiller.py", "src/gcs/lsp_bridge.py"])
