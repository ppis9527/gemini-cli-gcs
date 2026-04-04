import os
import json

class GCSRehydrator:
    def __init__(self, checkpoint_path):
        self.checkpoint_path = checkpoint_path
        self.checkpoint = self._load_checkpoint()

    def _load_checkpoint(self):
        if os.path.exists(self.checkpoint_path):
            with open(self.checkpoint_path, "r") as f:
                return json.load(f)
        return {}

    def get_source_map(self, file_path):
        return self.checkpoint.get("source_maps", {}).get(file_path, [])

    def is_skeletonized(self, file_path):
        return file_path in self.checkpoint.get("skeletons", {})

    def rehydrate_block(self, file_path, symbol_name):
        """
        Returns the original source code block for a given symbol.
        """
        source_map = self.get_source_map(file_path)
        metadata = next((m for m in source_map if m["symbol"] == symbol_name), None)
        
        if not metadata or not os.path.exists(file_path):
            return None

        with open(file_path, "rb") as f:
            f.seek(metadata["original_start"])
            content = f.read(metadata["original_end"] - metadata["original_start"])
            return content.decode("utf-8")

    def rehydrate_full_file(self, file_path):
        """
        Simple restoration: returns the full original file from disk.
        Since GCS doesn't delete original files, re-hydration is just 
        returning the actual file content to replace the skeleton in context.
        """
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return f.read()
        return None

if __name__ == "__main__":
    # Test placeholder
    rehydrator = GCSRehydrator(".gemini/checkpoint.json")
    print(f"Is Distiller skeletonized? {rehydrator.is_skeletonized('src/gcs/gcs_distiller.py')}")
