import os
import json
import threading

class GCSRehydrator:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, checkpoint_path):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GCSRehydrator, cls).__new__(cls)
                cls._instance.checkpoint_path = checkpoint_path
                cls._instance.checkpoint = cls._instance._load_checkpoint()
            return cls._instance

    def __init__(self, checkpoint_path):
        # Initialization is now safely handled entirely within __new__'s lock
        pass

    def _load_checkpoint(self):
        if os.path.exists(self.checkpoint_path):
            try:
                with open(self.checkpoint_path, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def is_skeletonized(self, file_path):
        # Normalize to realpath for symlink safety
        real_target = os.path.realpath(file_path)
        rel_target = os.path.relpath(real_target, self.checkpoint.get("project_root", os.getcwd()))
        return rel_target in self.checkpoint.get("skeletons", {})

    def rehydrate_block(self, file_path, symbol_name):
        real_path = os.path.realpath(file_path)
        rel_path = os.path.relpath(real_path, self.checkpoint.get("project_root", os.getcwd()))
        source_map = self.checkpoint.get("source_maps", {}).get(rel_path, [])
        metadata = next((m for m in source_map if m["symbol"] == symbol_name), None)
        
        if not metadata or not os.path.exists(real_path):
            return None

        # Verify file size to detect drift
        current_size = os.path.getsize(real_path)
        if metadata.get("file_size_at_distill") and current_size != metadata["file_size_at_distill"]:
            # Drift detected
            return None

        try:
            with open(real_path, "rb") as f:
                f.seek(metadata["original_start"])
                content = f.read(metadata["original_end"] - metadata["original_start"])
                # Safe decoding with replacement for non-UTF8
                return content.decode("utf-8", errors="replace")
        except (IOError, UnicodeDecodeError):
            return None

    def rehydrate_full_file(self, file_path):
        real_path = os.path.realpath(file_path)
        if os.path.exists(real_path):
            try:
                with open(real_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except Exception:
                return None
        return None
