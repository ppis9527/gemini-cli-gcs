import time
import os
import sys
from gcs_distiller import GCSDistiller

class SSTBench:
    def __init__(self, distiller):
        self.distiller = distiller

    def run_benchmark(self, file_path):
        with open(file_path, "r") as f:
            original_code = f.read()

        # Step 1: Baseline
        original_size = len(original_code.encode("utf-8"))
        
        # Step 2: Distillation
        start_time = time.perf_counter()
        distilled_code = self.distiller.skeletonize(file_path, original_code)
        distillation_time = (time.perf_counter() - start_time) * 1000  # ms
        
        distilled_size = len(distilled_code.encode("utf-8"))
        
        # Calculation
        compression_ratio = distilled_size / original_size if original_size > 0 else 1
        
        print(f"File: {file_path}")
        print(f"Original Size:  {original_size} bytes")
        print(f"Distilled Size: {distilled_size} bytes (Aligned)")
        print(f"Ratio:          {compression_ratio:.2%}")
        print(f"Latency:        {distillation_time:.2f} ms")
        print("-" * 20)

if __name__ == "__main__":
    distiller = GCSDistiller()
    bench = SSTBench(distiller)
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            if os.path.exists(path):
                bench.run_benchmark(path)
