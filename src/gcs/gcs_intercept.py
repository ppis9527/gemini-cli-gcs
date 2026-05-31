import os
import sys
import argparse

# Ensure src directory is in sys.path when run as a script.
_current_dir = os.path.dirname(os.path.abspath(__file__))
_src_root = os.path.dirname(_current_dir)
if _src_root not in sys.path:
    sys.path.insert(0, _src_root)

from gcs.gcs_rehydrator import GCSRehydrator

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-intent", action="store_true")
    parser.add_argument("--file", action="append", default=[])
    args = parser.parse_args()

    intercept = GCSIntercept(os.getcwd())
    if args.check_intent:
        needs_rehydration = False
        for target in args.file:
            if intercept.pre_tool_hook("intent_check", {"file_path": target}):
                needs_rehydration = True
                break
        if needs_rehydration:
            print("RE-HYDRATION_REQUIRED")
        else:
            print("GCS_INTERCEPT: Intent checking enabled. Ready for analysis.")
    else:
        # Test simulation
        intercept.pre_tool_hook("read_file", {"file_path": "src/gcs/gcs_distiller.py"})
