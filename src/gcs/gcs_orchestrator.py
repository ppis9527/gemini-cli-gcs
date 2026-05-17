import os
import sys
import json
import time
import subprocess
import fcntl
import zlib
import base64

from gcs.gcs_distiller import GCSDistiller
from gcs.config import get_paths, THRESHOLD_TOKENS, SMALL_FILE_THRESHOLD, __version__

class GCSOrchestrator:
    def __init__(self, root_path, threshold=THRESHOLD_TOKENS):
        self.root_path = root_path
        self.threshold = threshold
        self.paths = get_paths(root_path)
        os.makedirs(self.paths["dot_gemini"], exist_ok=True)
        self.checkpoint_path = str(self.paths["checkpoint"])
        self.lock_path = str(self.paths["lock"])
        self.log_path = str(self.paths["log"])
        self.pending_path = str(self.paths["pending"])

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
            with open(self.checkpoint_path, "rb") as f:
                raw = f.read()
            try:
                decoded = zlib.decompress(base64.b64decode(raw)).decode("utf-8")
                checkpoint = json.loads(decoded)
            except Exception:
                checkpoint = json.loads(raw.decode("utf-8"))

            try:
                current_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root_path, text=True).strip()
            except Exception:
                current_sha = "no-git-repo"
            
            if checkpoint.get("commit_sha") != current_sha:
                self._log(f"Branch change detected ({checkpoint.get('commit_sha')} -> {current_sha}). Purging skeletons.")
                checkpoint["skeletons"] = {}
                checkpoint["source_maps"] = {}
            else:
                checkpoint["skeletons"] = {k: v for k, v in checkpoint.get("skeletons", {}).items() 
                                          if os.path.exists(os.path.join(self.root_path, k)) or k.startswith("COMMON_BUCKET_")}
                checkpoint["source_maps"] = {k: v for k, v in checkpoint.get("source_maps", {}).items() 
                                            if os.path.exists(os.path.join(self.root_path, k))}
            
            self._save_checkpoint(checkpoint)
        except Exception as e:
            self._log(f"Cleanup failed: {e}")

    def _save_checkpoint(self, checkpoint):
        tmp_checkpoint = self.checkpoint_path + ".tmp"
        with open(tmp_checkpoint, "wb") as f:
            json_str = json.dumps(checkpoint, indent=2)
            f.write(base64.b64encode(zlib.compress(json_str.encode("utf-8"))))
        os.rename(tmp_checkpoint, self.checkpoint_path)

    def run_distillation(self, active_files):
        index_lock = os.path.join(self.root_path, ".git", "index.lock")
        if os.path.exists(index_lock):
            self._log("Git index locked, postponing.")
            return False
        
        try:
            lock_f = open(self.lock_path, "a")
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
                abs_f_path = os.path.join(self.root_path, f_path) if not os.path.isabs(f_path) else f_path
                rel_f_path = os.path.relpath(abs_f_path, self.root_path)
                
                if os.path.exists(abs_f_path):
                    with open(abs_f_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    skele_content, s_map = distiller.skeletonize(abs_f_path, content, skip_alignment=True)
                    source_maps[rel_f_path] = s_map
                    if len(skele_content.encode("utf-8")) < SMALL_FILE_THRESHOLD:
                        small_skeletons[rel_f_path] = skele_content
                    else:
                        skeletons[rel_f_path] = distiller._apply_hysteresis(skele_content)
            
            if small_skeletons:
                packed = distiller.pack_skeletons(small_skeletons)
                for idx, bucket in enumerate(packed):
                    skeletons[f"COMMON_BUCKET_{idx}"] = bucket
            
            try:
                commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root_path, text=True).strip()
            except Exception:
                commit_sha = "no-git-repo"
            
            checkpoint = {
                "gcs_version": __version__,
                "timestamp": time.time(),
                "commit_sha": commit_sha,
                "project_root": self.root_path,
                "skeletons": skeletons,
                "source_maps": source_maps
            }
            
            self._save_checkpoint(checkpoint)
            duration = (time.perf_counter() - start_time) * 1000
            self._log(f"Distillation complete in {duration:.2f}ms.")

            state = {
                "last_active_step": "DISTILLATION_COMPLETE",
                "timestamp": time.time(),
                "resume_task": "GCS_GOVERNANCE_AUTO"
            }
            with open(self.pending_path, "w") as f:
                json.dump(state, f)

            return True
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)
            lock_f.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="GCS Orchestrator")
    parser.add_argument("--background", action="store_true", help="Run in YOLO background mode")
    parser.add_argument("--tokens", type=int, default=0, help="Current token count")
    parser.add_argument("--files", nargs="*", default=[], help="Files to distill")
    args = parser.parse_args()

    orchestrator = GCSOrchestrator(os.getcwd())
    
    if args.background:
        # YOLO mode: scan git-tracked files
        try:
            tracked = subprocess.check_output(
                ["git", "ls-files", "--", "*.py", "*.js", "*.ts", "*.tsx"],
                cwd=os.getcwd(), text=True
            ).splitlines()
        except Exception:
            tracked = []
        if hasattr(os, "nice"):
            os.nice(10)  # Lower priority in background
        orchestrator.run_distillation(tracked)
    elif args.tokens > 0:
        if orchestrator.should_distill(args.tokens):
            files = args.files if args.files else []
            orchestrator.run_distillation(files)
    elif args.files:
        orchestrator.run_distillation(args.files)

if __name__ == "__main__":
    main()
