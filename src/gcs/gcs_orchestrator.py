from concurrent.futures import ProcessPoolExecutor
import functools
import os
import sys

# Ensure src directory is in sys.path for relative imports to work when run as script
_current_dir = os.path.dirname(os.path.abspath(__file__))
_src_root = os.path.dirname(_current_dir)
if _src_root not in sys.path:
    sys.path.insert(0, _src_root)

import json
import time
import subprocess
import fcntl
import zlib
import base64

_worker_distiller = None

def _init_worker():
    global _worker_distiller
    try:
        from gcs.gcs_distiller import GCSDistiller
        _worker_distiller = GCSDistiller()
    except Exception:
        pass

def _distill_worker(f_path, root_path):
    global _worker_distiller
    if _worker_distiller is None:
        _init_worker()
    if _worker_distiller is None:
        return None
    try:
        abs_f_path = os.path.join(root_path, f_path) if not os.path.isabs(f_path) else f_path
        rel_f_path = os.path.relpath(abs_f_path, root_path)
        if os.path.exists(abs_f_path):
            with open(abs_f_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            skele_content, s_map = _worker_distiller.skeletonize(abs_f_path, content, skip_alignment=True)
            return rel_f_path, skele_content, s_map
    except Exception:
        return None
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
                current_sha = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.root_path,
                    text=True,
                    stderr=subprocess.DEVNULL
                ).strip()
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

    main()
    def run_distillation(self, active_files, incremental=True):
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
            
            # Load existing checkpoint for incremental merge
            checkpoint = {"skeletons": {}, "source_maps": {}}
            if incremental and os.path.exists(self.checkpoint_path):
                try:
                    with open(self.checkpoint_path, "rb") as f:
                        raw = f.read()
                    decoded = zlib.decompress(base64.b64decode(raw)).decode("utf-8")
                    checkpoint = json.loads(decoded)
                except Exception: pass

            self._log(f"Starting distillation for {len(active_files)} files (incremental={incremental}).")
            start_time = time.perf_counter()
            distiller = GCSDistiller()
            
            # Limit workers to prevent I/O saturation on high-core systems
            max_workers = min(32, os.cpu_count() or 4)
            with ProcessPoolExecutor(max_workers=max_workers, initializer=_init_worker) as executor:
                results = list(executor.map(functools.partial(_distill_worker, root_path=self.root_path), active_files))
            
            new_skeletons = {}
            small_skeletons = {}
            for res in results:
                if res:
                    rel_f_path, skele_content, s_map = res
                    checkpoint["source_maps"][rel_f_path] = s_map
                    if len(skele_content.encode("utf-8")) < SMALL_FILE_THRESHOLD:
                        small_skeletons[rel_f_path] = skele_content
                    else:
                        checkpoint["skeletons"][rel_f_path] = distiller._apply_hysteresis(skele_content)
            
            if small_skeletons:
                packed = distiller.pack_skeletons(small_skeletons)
                for idx, bucket in enumerate(packed):
                    checkpoint["skeletons"][f"COMMON_BUCKET_{idx}"] = bucket
            
            try:
                commit_sha = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=self.root_path, text=True, stderr=subprocess.DEVNULL
                ).strip()
            except Exception: commit_sha = "no-git-repo"
            
            checkpoint.update({
                "gcs_version": __version__,
                "timestamp": time.time(),
                "commit_sha": commit_sha,
                "project_root": self.root_path,
            })
            
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
    parser.add_argument("--full", action="store_true", help="Force full scan (disables incremental)")
    parser.add_argument("--tokens", type=int, default=0, help="Current token count")
    parser.add_argument("--files", nargs="*", default=[], help="Files to distill")
    args = parser.parse_args()

    orchestrator = GCSOrchestrator(os.getcwd())
    incremental = not args.full
    
    if args.background:
        try:
            if incremental:
                # Incremental: only changed/new files
                tracked = subprocess.check_output(
                    ["git", "diff", "--name-only", "HEAD", "--", "*.py", "*.js", "*.ts", "*.tsx"],
                    cwd=os.getcwd(), text=True, stderr=subprocess.DEVNULL
                ).splitlines()
                # Also include untracked but tracked-type files
                tracked += subprocess.check_output(
                    ["git", "ls-files", "--others", "--exclude-standard", "--", "*.py", "*.js", "*.ts", "*.tsx"],
                    cwd=os.getcwd(), text=True, stderr=subprocess.DEVNULL
                ).splitlines()
            else:
                tracked = subprocess.check_output(
                    ["git", "ls-files", "--", "*.py", "*.js", "*.ts", "*.tsx"],
                    cwd=os.getcwd(), text=True, stderr=subprocess.DEVNULL
                ).splitlines()
        except Exception:
            tracked = []
        
        if hasattr(os, "nice"): os.nice(10)
        orchestrator.run_distillation(list(set(tracked)), incremental=incremental)
    elif args.tokens > 0:
        if orchestrator.should_distill(args.tokens):
            orchestrator.run_distillation(args.files if args.files else [], incremental=incremental)
    elif args.files:
        orchestrator.run_distillation(args.files, incremental=incremental)
