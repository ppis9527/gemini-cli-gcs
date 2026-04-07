import os
import sys
import json
import time
import subprocess
import fcntl
from gcs_distiller import GCSDistiller

class GCSOrchestrator:
    def __init__(self, root_path, threshold=200000):
        self.root_path = root_path
        self.threshold = threshold
        self.dot_gemini = os.path.join(root_path, ".gemini")
        os.makedirs(self.dot_gemini, exist_ok=True)
        self.checkpoint_path = os.path.join(self.dot_gemini, "checkpoint.json")
        self.lock_path = os.path.join(self.dot_gemini, "gcs.lock")
        self.log_path = os.path.join(self.dot_gemini, "gcs.log")

    def _log(self, message):
        try:
            if os.path.exists(self.log_path) and os.path.getsize(self.log_path) > 1024 * 1024:
                os.rename(self.log_path, self.log_path + ".old")
        except Exception:
            pass
        with open(self.log_path, "a") as f:
            f.write(f"[{time.ctime()}] {message}\n")

    def should_distill(self, current_tokens):
        return current_tokens >= self.threshold

    def cleanup_stale_entries(self):
        if not os.path.exists(self.checkpoint_path):
            return
        try:
            with open(self.checkpoint_path, "r") as f:
                checkpoint = json.load(f)
            try:
                current_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root_path, text=True).strip()
            except Exception:
                current_sha = "no-git-repo"
            if checkpoint.get("commit_sha") != current_sha:
                self._log(f"Branch change detected. Purging skeletons.")
                checkpoint["skeletons"] = {}
                checkpoint["source_maps"] = {}
            else:
                checkpoint["skeletons"] = {k: v for k, v in checkpoint.get("skeletons", {}).items() 
                                          if os.path.exists(k) or k.startswith("COMMON_BUCKET_")}
                # Sync source maps
                checkpoint["source_maps"] = {k: v for k, v in checkpoint.get("source_maps", {}).items() if os.path.exists(k)}
            with open(self.checkpoint_path, "w") as f:
                json.dump(checkpoint, f, indent=2)
        except Exception as e:
            self._log(f"Cleanup failed: {e}")

    def run_distillation(self, active_files):
        index_lock = os.path.join(self.root_path, ".git", "index.lock")
        if os.path.exists(index_lock):
            self._log("Git index locked, postponing.")
            return False
        try:
            lock_f = open(self.lock_path, "a") # Changed from "w" to "a"
            fcntl.flock(lock_f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError, OSError):
            self._log("Distillation in progress, skipping.")
            return False
        try:
            self.cleanup_stale_entries()
            self._log(f"Starting auto-distillation for {len(active_files)} files.")
            start_time = time.perf_counter()
            distiller = GCSDistiller()
            skeletons = {}
            source_maps = {}
            small_skeletons = {}
            for f_path in active_files:
                if os.path.exists(f_path):
                    with open(f_path, "r") as f:
                        content = f.read()
                    skele_content, s_map = distiller.skeletonize(f_path, content, skip_alignment=True)
                    source_maps[f_path] = s_map
                    if len(skele_content.encode("utf-8")) < 1024:
                        small_skeletons[f_path] = skele_content
                    else:
                        skeletons[f_path] = distiller._apply_hysteresis(skele_content)
            if small_skeletons:
                packed = distiller.pack_skeletons(small_skeletons)
                for idx, bucket in enumerate(packed):
                    skeletons[f"COMMON_BUCKET_{idx}"] = bucket
            try:
                commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root_path, text=True).strip()
            except Exception:
                commit_sha = "no-git-repo"
            checkpoint = {
                "gcs_version": "1.13",
                "timestamp": time.time(),
                "commit_sha": commit_sha,
                "project_root": self.root_path,
                "skeletons": skeletons,
                "source_maps": source_maps
            }
            tmp_checkpoint = self.checkpoint_path + ".tmp"
            with open(tmp_checkpoint, "w") as f:
                json.dump(checkpoint, f, indent=2)
            os.rename(tmp_checkpoint, self.checkpoint_path)
            duration = (time.perf_counter() - start_time) * 1000
            self._log(f"Distillation complete in {duration:.2f}ms.")

            # --- WAS (Write-Ahead State) Implementation ---
            pending_path = os.path.join(self.dot_gemini, "gcs.pending")
            state = {
                "last_active_step": "DISTILLATION_COMPLETE",
                "timestamp": time.time(),
                "resume_task": "GCS_GOVERNANCE_AUTO"
            }
            with open(pending_path, "w") as f:
                json.dump(state, f)
            # -----------------------------------------------

            return True
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)
            lock_f.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        tokens = int(sys.argv[1])
        orchestrator = GCSOrchestrator(os.getcwd())
        if orchestrator.should_distill(tokens):
            orchestrator.run_distillation(["src/gcs/gcs_distiller.py", "src/gcs/lsp_bridge.py"])
