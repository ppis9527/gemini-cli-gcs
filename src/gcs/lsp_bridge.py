import os
import sys
import json
import time
import subprocess
import threading
import queue

class LSPBridge:
    def __init__(self, root_uri, lsp_command, max_cache_size=1000):
        self.root_uri = root_uri
        self.lsp_command = lsp_command
        self.max_cache_size = max_cache_size
        self.process = None
        self.id_counter = 0
        self.responses = {}
        self.lock = threading.Lock()
        self.l1_cache = {} # Symbol Cache: {key: {"result": r, "count": c}}

    def start(self):
        self.process = subprocess.Popen(
            self.lsp_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        threading.Thread(target=self._listen, daemon=True).start()
        self.initialize()

    def _listen(self):
        while self.process and self.process.poll() is None:
            line = self.process.stdout.readline()
            if not line: break
            if line.startswith("Content-Length:"):
                length = int(line.split(":")[1].strip())
                while True:
                    next_line = self.process.stdout.readline()
                    if next_line == "\r\n" or next_line == "\n":
                        break
                body = self.process.stdout.read(length)
                try:
                    resp = json.loads(body)
                    if "id" in resp:
                        with self.lock:
                            self.responses[resp["id"]] = resp
                except json.JSONDecodeError:
                    continue

    def _send(self, method, params=None):
        with self.lock:
            msg_id = self.id_counter
            self.id_counter += 1
        payload = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
            "params": params or {}
        }
        body = json.dumps(payload)
        msg = f"Content-Length: {len(body)}\r\n\r\n{body}"
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(msg)
                self.process.stdin.flush()
            except BrokenPipeError:
                pass
        return msg_id

    def initialize(self):
        msg_id = self._send("initialize", {
            "processId": os.getpid(),
            "rootUri": self.root_uri,
            "capabilities": {}
        })
        self._wait_for_response(msg_id, timeout=2.0)

    def _wait_for_response(self, msg_id, timeout=0.2):
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < timeout:
            with self.lock:
                if msg_id in self.responses:
                    return self.responses.pop(msg_id)
            time.sleep(0.01)
        
        with self.lock:
            self.responses.pop(msg_id, None)
        return None

    def _evict_cache(self):
        if len(self.l1_cache) > self.max_cache_size:
            with self.lock:
                items = list(self.l1_cache.items())
            items.sort(key=lambda x: x[1]["count"])
            evict_count = self.max_cache_size // 10
            keys_to_remove = [x[0] for x in items[:evict_count]]
            with self.lock:
                for k in keys_to_remove:
                    self.l1_cache.pop(k, None)

    def _ensure_process(self):
        with self.lock:
            if self.process is None or self.process.poll() is not None:
                self.start()

    def query_definition(self, file_uri, line, character):
        self._ensure_process()
        cache_key = f"{file_uri}:{line}:{character}"
        if cache_key in self.l1_cache:
            with self.lock:
                self.l1_cache[cache_key]["count"] += 1
                return self.l1_cache[cache_key]["result"], "L1", self.l1_cache[cache_key]["count"]

        msg_id = self._send("textDocument/definition", {
            "textDocument": {"uri": file_uri},
            "position": {"line": line, "character": character}
        })
        resp = self._wait_for_response(msg_id, timeout=0.2)
        if resp and "result" in resp:
            self._evict_cache()
            with self.lock:
                self.l1_cache[cache_key] = {"result": resp["result"], "count": 1}
                return resp["result"], "L2", 1
        return None, "L3", 0

    def stop(self):
        if self.process:
            self.process.terminate()

if __name__ == "__main__":
    bridge = LSPBridge(f"file://{os.getcwd()}", ["venv/bin/pylsp"])
    bridge.start()
    print("LSP Bridge Started.")
    time.sleep(1)
    bridge.stop()
