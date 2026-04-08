import os
import sys
import json
import subprocess
import threading
import time
from typing import Optional, Tuple, Any

from gcs.config import LSP_CACHE_MAX, LSP_EVICT_RATIO, LSP_RESPONSE_TIMEOUT

class LSPBridge:
    def __init__(self, root_uri: str, command: list[str]):
        self.root_uri = root_uri
        self.command = command
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        self.responses = {}
        self.lock = threading.Lock()
        self.l1_cache = {}
        self.is_running = False

    def start(self):
        try:
            self.process = subprocess.Popen(
                self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=False
            )
            self.is_running = True
            threading.Thread(target=self._read_loop, daemon=True).start()
            self._initialize()
        except Exception as e: print(f"GCS LSP: Failed to start server: {e}")

    def _initialize(self):
        self._send({
            "jsonrpc": "2.0", "id": 0, "method": "initialize",
            "params": {"processId": os.getpid(), "rootUri": self.root_uri, "capabilities": {}}
        })

    def _send(self, payload):
        if not self.process or not self.process.stdin: return
        body = json.dumps(payload).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
        with self.lock:
            try:
                self.process.stdin.write(header + body)
                self.process.stdin.flush()
            except BrokenPipeError: self.is_running = False

    def _read_loop(self):
        while self.is_running and self.process and self.process.stdout:
            try:
                line = self.process.stdout.readline().decode("utf-8")
                if not line.startswith("Content-Length:"): continue
                length = int(line.split(":")[1].strip())
                self.process.stdout.readline()
                body = self.process.stdout.read(length).decode("utf-8")
                response = json.loads(body)
                if "id" in response:
                    with self.lock: self.responses[response["id"]] = response
            except Exception: break

    def query_definition(self, file_uri: str, line: int, character: int) -> Tuple[Optional[dict], str, int]:
        cache_key = f"{file_uri}:{line}:{character}"
        with self.lock:
            if cache_key in self.l1_cache:
                self.l1_cache[cache_key]["count"] += 1
                return self.l1_cache[cache_key]["result"], "L1", self.l1_cache[cache_key]["count"]
            self.request_id += 1
            msg_id = self.request_id

        self._send({
            "jsonrpc": "2.0", "id": msg_id, "method": "textDocument/definition",
            "params": {"textDocument": {"uri": file_uri}, "position": {"line": line, "character": character}}
        })

        start = time.time()
        while time.time() - start < LSP_RESPONSE_TIMEOUT:
            with self.lock:
                if msg_id in self.responses:
                    res = self.responses.pop(msg_id)
                    result = res.get("result")
                    self._update_cache(cache_key, result)
                    return result, "L2", 1
            time.sleep(0.01)
        return None, "MISS", 0

    def _update_cache(self, key, result):
        with self.lock:
            if len(self.l1_cache) >= LSP_CACHE_MAX:
                sorted_keys = sorted(self.l1_cache.keys(), key=lambda k: self.l1_cache[k]["count"])
                for k in sorted_keys[:int(LSP_CACHE_MAX * LSP_EVICT_RATIO)]: del self.l1_cache[k]
            self.l1_cache[key] = {"result": result, "count": 1}

    def stop(self):
        self.is_running = False
        if self.process: self.process.terminate(); self.process = None

if __name__ == "__main__":
    bridge = LSPBridge(f"file://{os.getcwd()}", ["pylsp"]); bridge.start()
    time.sleep(1); res = bridge.query_definition(f"file://{os.path.abspath(__file__)}", 10, 5)
    print(f"LSP Result: {res}"); bridge.stop()
