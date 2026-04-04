import os
import sys
import subprocess
import json
from datetime import datetime
from gcs_distiller import GCSDistiller

class GCSHealthReport:
    def __init__(self, root_path):
        self.root_path = root_path
        self.distiller = GCSDistiller()
        self.results = []

    def scan_repo(self):
        print(f"Scanning repository: {self.root_path}")
        files = []
        try:
            # Try git ls-files first
            files = subprocess.check_output(
                ["git", "ls-files"], 
                cwd=self.root_path, 
                text=True,
                stderr=subprocess.DEVNULL
            ).splitlines()
        except subprocess.CalledProcessError:
            # Fallback for non-git: manual walk
            print("Non-git repo detected, falling back to manual walk.")
            exclude_dirs = {".git", "node_modules", "venv", ".venv", "__pycache__", ".gemini", "dist", "build"}
            for root, dirs, filenames in os.walk(self.root_path):
                # In-place modification to skip directories
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                for f in filenames:
                    rel_path = os.path.relpath(os.path.join(root, f), self.root_path)
                    files.append(rel_path)

        for rel_path in files:
            if rel_path.endswith((".py", ".js", ".ts", ".tsx")):
                abs_path = os.path.join(self.root_path, rel_path)
                self._process_file(abs_path, rel_path)

    def _process_file(self, abs_path, rel_path):
        try:
            with open(abs_path, "r") as f:
                content = f.read()
            
            orig_size = len(content.encode("utf-8"))
            if orig_size == 0: return

            distilled = self.distiller.skeletonize(abs_path, content)
            dist_size = len(distilled.encode("utf-8"))
            
            self.results.append({
                "file": rel_path,
                "original": orig_size,
                "distilled": dist_size,
                "saving": orig_size - dist_size
            })
        except Exception:
            pass

    def generate_report(self, output_path):
        total_orig = sum(r["original"] for r in self.results)
        total_dist = sum(r["distilled"] for r in self.results)
        total_saving = total_orig - total_dist
        saving_pct = (total_saving / total_orig * 100) if total_orig > 0 else 0

        report = [
            "# GCS Context Health Report (Git-Aware)",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n## Summary",
            f"- **Total Source Files (Git)**: {len(self.results)}",
            f"- **Total Original Size**: {total_orig / 1024:.2f} KB",
            f"- **Total Distilled Size**: {total_dist / 1024:.2f} KB (Aligned)",
            f"- **Potential Token Saving**: {total_saving / 1024:.2f} KB ({saving_pct:.2f}%)",
            "\n## Top 30 Optimization Targets",
            "| File | Original (B) | Distilled (B) | Saving (%) |",
            "| :--- | :--- | :--- | :--- |"
        ]

        # Sort by saving amount
        sorted_results = sorted(self.results, key=lambda x: x["saving"], reverse=True)
        for r in sorted_results[:30]:
            pct = (r["saving"] / r["original"] * 100) if r["original"] > 0 else 0
            report.append(f"| {r['file']} | {r['original']} | {r['distilled']} | {pct:.1f}% |")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write("\n".join(report))
        print(f"Health Report saved to: {output_path}")

if __name__ == "__main__":
    reporter = GCSHealthReport(os.getcwd())
    reporter.scan_repo()
    reporter.generate_report("docs/gcs/health_report_2026-04-04.md")
