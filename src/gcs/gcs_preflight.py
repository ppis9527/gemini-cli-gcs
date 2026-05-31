#!/usr/bin/env python3
import argparse
import importlib
import json
import os
import sys


REQUIRED_MODULES = [
    "tree_sitter",
    "tree_sitter_python",
    "tree_sitter_javascript",
    "tree_sitter_typescript",
]


def check_dependencies():
    missing = []
    for mod in REQUIRED_MODULES:
        try:
            importlib.import_module(mod)
        except Exception:
            missing.append(mod)
    return missing


def main():
    parser = argparse.ArgumentParser(description="GCS Preflight checks")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    args = parser.parse_args()

    missing = check_dependencies()
    ok = len(missing) == 0
    result = {
        "ok": ok,
        "missing_modules": missing,
        "cwd": os.getcwd(),
    }

    if args.json:
        print(json.dumps(result))
    else:
        if ok:
            print("GCS_PREFLIGHT_OK")
        else:
            print(f"GCS_PREFLIGHT_MISSING: {', '.join(missing)}")

    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
