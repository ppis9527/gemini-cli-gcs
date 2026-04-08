import os
import sys
import tree_sitter
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript
import re
from math import log2

from gcs.lsp_bridge import LSPBridge
from gcs.config import (
    BUCKET_SIZE, BUCKET_SLACK, HOT_SYMBOL_QUERY_THRESHOLD, 
    HOT_SYMBOL_PRESERVED_LINES, AST_NODE_LIMIT, SECRET_PATTERNS
)

class GCSDistiller:
    def __init__(self, use_lsp=False, root_path=None):
        self.languages = {
            ".py": tree_sitter.Language(tree_sitter_python.language()),
            ".js": tree_sitter.Language(tree_sitter_javascript.language()),
            ".ts": tree_sitter.Language(tree_sitter_typescript.language_typescript()),
            ".tsx": tree_sitter.Language(tree_sitter_typescript.language_tsx()),
        }
        self.parsers = {ext: tree_sitter.Parser(lang) for ext, lang in self.languages.items()}
        self.use_lsp = use_lsp
        self.lsp_bridge = None
        if use_lsp and root_path:
            venv_path = os.path.join(root_path, ".gemini", "gcs-venv", "bin", "pylsp")
            self.lsp_bridge = LSPBridge(f"file://{root_path}", [venv_path])
            self.lsp_bridge.start()

    def skeletonize(self, file_path, source_code, skip_alignment=False):
        _, ext = os.path.splitext(file_path)
        parser = self.parsers.get(ext)
        if not parser:
            return (source_code, []) if skip_alignment else (self._apply_hysteresis(source_code), [])

        source_bytes_raw = source_code.encode("utf-8")
        tree = parser.parse(source_bytes_raw)
        root = tree.root_node

        # Circuit Breaker (Iterative count)
        node_count = self._count_nodes(root)
        if node_count > AST_NODE_LIMIT:
            summary = f"# [GCS CIRCUIT BREAKER] {file_path}\n# Nodes: {node_count} > {AST_NODE_LIMIT}\n# Size: {len(source_code)} bytes\n"
            return (summary, []) if skip_alignment else (self._apply_hysteresis(summary), [])

        edits = []
        source_map = []
        file_uri = f"file://{os.path.abspath(file_path)}"
        self._find_blocks_to_skeletonize(root, edits, ext, file_uri, source_code, source_map)
        
        source_bytes = bytearray(source_bytes_raw)
        for start_byte, end_byte, replacement in sorted(edits, key=lambda x: x[0], reverse=True):
            source_bytes[start_byte:end_byte] = replacement.encode("utf-8")
        
        distilled = source_bytes.decode("utf-8")
        final_output = distilled if skip_alignment else self._apply_hysteresis(distilled)
        return final_output, source_map

    def pack_skeletons(self, file_content_map, block_size=BUCKET_SIZE, slack=BUCKET_SLACK):
        buckets = []
        current_bucket_files = []
        current_bucket_content = ""
        def finalize_bucket(content, files):
            manifest = "<!-- GCS_BUCKET_MANIFEST_START: " + ", ".join(files) + " -->\n"
            footer = "\n<!-- GCS_BUCKET_MANIFEST_END -->"
            return self._apply_hysteresis(manifest + content + footer, block_size, slack)
        for file_path, content in file_content_map.items():
            _, ext = os.path.splitext(file_path)
            lang = ext.lstrip(".")
            entry = f"\n--- GCS_FILE_START: {file_path} ---\n```{lang}\n{content}\n```\n--- GCS_FILE_END: {file_path} ---"
            if len((current_bucket_content + entry).encode("utf-8")) + 256 + slack > block_size:
                if current_bucket_content:
                    buckets.append(finalize_bucket(current_bucket_content, current_bucket_files))
                current_bucket_content = entry
                current_bucket_files = [file_path]
            else:
                current_bucket_content += entry
                current_bucket_files.append(file_path)
        if current_bucket_content:
            buckets.append(finalize_bucket(current_bucket_content, current_bucket_files))
        return buckets

    def _apply_hysteresis(self, text, block_size=BUCKET_SIZE, slack=BUCKET_SLACK):
        size = len(text.encode("utf-8"))
        aligned_size = ((size + slack + block_size - 1) // block_size) * block_size
        padding_needed = aligned_size - size
        comment_header = "<!-- GCS_HYSTERESIS_PADDING_"
        comment_footer = " -->"
        min_comment_len = len(f"\n{comment_header}{padding_needed}{comment_footer}".encode("utf-8"))
        if padding_needed >= min_comment_len:
            padding = f"\n{comment_header}{padding_needed}{comment_footer}"
            padding += " " * (padding_needed - len(padding.encode("utf-8")))
        else:
            padding = " " * padding_needed
        return text + padding

    def _count_nodes(self, node):
        count = 0
        stack = [node]
        while stack:
            curr = stack.pop()
            count += 1
            for i in range(curr.child_count):
                stack.append(curr.child(i))
        return count

    def _shannon_entropy(self, s):
        freq = {}
        for c in s:
            freq[c] = freq.get(c, 0) + 1
        length = len(s)
        if length == 0: return 0
        return -sum((f/length) * log2(f/length) for f in freq.values())

    def _scrub_secrets(self, node, edits, source_code):
        if node.type in ("string", "template_string", "string_literal"):
            try:
                text = source_code.encode("utf-8")[node.start_byte:node.end_byte].decode("utf-8")
            except Exception: return
            for pattern in SECRET_PATTERNS:
                if re.search(pattern, text):
                    edits.append((node.start_byte, node.end_byte, '"[REDACTED]"'))
                    return
            parent = node.parent
            if parent and parent.type in ("assignment", "variable_declarator", "pair"):
                context_text = ""
                for child in parent.children:
                    if child.type in ("identifier", "property_identifier", "variable_name"):
                        try: context_text += source_code.encode("utf-8")[child.start_byte:child.end_byte].decode("utf-8")
                        except Exception: pass
                for pattern in SECRET_PATTERNS:
                    if re.search(pattern, context_text):
                        edits.append((node.start_byte, node.end_byte, '"[REDACTED]"'))
                        return
            inner_text = text.strip("\"' ")
            if len(inner_text) > 32 and self._shannon_entropy(inner_text) > 4.5:
                edits.append((node.start_byte, node.end_byte, '"[REDACTED_HIGH_ENTROPY]"'))

    def _find_blocks_to_skeletonize(self, node, edits, ext, file_uri, source_code, source_map):
        self._scrub_secrets(node, edits, source_code)
        func_types = ("function_definition", "function_declaration", "method_definition", "arrow_function", "generator_function_declaration")
        if node.type in func_types:
            symbol_name = "anonymous"
            for child in node.children:
                if child.type in ("identifier", "property_identifier"):
                    try: symbol_name = source_code.encode("utf-8")[child.start_byte:child.end_byte].decode("utf-8")
                    except Exception: pass
                    break
            semantic_hint = ""; is_hot = False
            if self.lsp_bridge:
                res, tier, count = self.lsp_bridge.query_definition(file_uri, node.start_point[0], node.start_point[1])
                if tier in ("L1", "L2") and res:
                    is_hot = count >= HOT_SYMBOL_QUERY_THRESHOLD
                    hot_tag = " [HOT_SYMBOL]" if is_hot else ""
                    semantic_hint = f" # [SEMANTIC_{tier}]{hot_tag}"
            body_node = None
            for child in node.children:
                if child.type in ("block", "statement_block"):
                    body_node = child
                    break
            if body_node:
                source_map.append({
                    "symbol": symbol_name, "original_start": body_node.start_byte,
                    "original_end": body_node.end_byte, "type": node.type,
                    "file_size_at_distill": len(source_code.encode("utf-8"))
                })
                if is_hot:
                    try:
                        body_text = source_code.encode("utf-8")[body_node.start_byte:body_node.end_byte].decode("utf-8")
                        body_lines = body_text.splitlines()
                        preserved_count = min(len(body_lines), HOT_SYMBOL_PRESERVED_LINES)
                        preserved_body = "\n".join(body_lines[:preserved_count]) + "\n        ... (semantic truncation)"
                        replacement = f" {preserved_body}"
                    except Exception: replacement = f" pass{semantic_hint}" if ext == ".py" else f" ...{semantic_hint}"
                else: replacement = f" pass{semantic_hint}" if ext == ".py" else f" ...{semantic_hint}"
                edits.append((body_node.start_byte, body_node.end_byte, replacement))
                return
        for child in node.children: self._find_blocks_to_skeletonize(child, edits, ext, file_uri, source_code, source_map)

    def stop(self):
        if self.lsp_bridge: self.lsp_bridge.stop(); self.lsp_bridge = None

    def __del__(self): self.stop()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="GCS Distiller CLI")
    parser.add_argument("file", help="File to skeletonize")
    args = parser.parse_args()
    distiller = GCSDistiller()
    if os.path.exists(args.file):
        with open(args.file, "r") as f: print(distiller.skeletonize(args.file, f.read())[0])

if __name__ == "__main__": main()
