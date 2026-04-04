import os
import sys
from gcs_rehydrator import GCSRehydrator

class GCSIntercept:
    def __init__(self, root_path):
        self.root_path = root_path
        self.checkpoint_path = os.path.join(root_path, ".gemini", "checkpoint.json")
        self.rehydrator = GCSRehydrator(self.checkpoint_path)

    def pre_tool_hook(self, tool_name, args):
        """
        Intercepts tool calls to skeletonized files.
        """
        target_file = args.get("file_path") or args.get("path")
        if not target_file:
            return

        # Use realpath for robust symlink handling
        abs_target = os.path.realpath(target_file)
        rel_target = os.path.relpath(abs_target, self.root_path)

        if self.rehydrator.is_skeletonized(rel_target):
            # LOG: Detected access to skeletonized file
            print(f"GCS: Intercepted {tool_name} for {rel_target}. Re-hydrating context...")
            # In Phase 7, we don't necessarily need to WRITE back to disk 
            # because the original file IS on disk.
            # We just need to ensure the Agent's PERCEPTION is correct.
            # This hook signals the orchestrator to provide full context.
            return True
        return False

if __name__ == "__main__":
    intercept = GCSIntercept(os.getcwd())
    # Test simulation
    intercept.pre_tool_hook("read_file", {"file_path": "src/gcs/gcs_distiller.py"})
