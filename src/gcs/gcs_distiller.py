import os
import sys
import tree_sitter
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript
from src.gcs.lsp_bridge import LSPBridge

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
            self.lsp_bridge = LSPBridge(f"file://{root_path}", ["venv/bin/pylsp"])
            self.lsp_bridge.start()

    def skeletonize(self, file_path, source_code, skip_alignment=False):
        _, ext = os.path.splitext(file_path)
        parser = self.parsers.get(ext)
        if not parser:
            return (source_code, []) if skip_alignment else (self._apply_hysteresis(source_code), [])

        tree = parser.parse(source_code.encode("utf-8"))
        root = tree.root_node

        edits = []
        source_map = []
        file_uri = f"file://{os.path.abspath(file_path)}"
        self._find_blocks_to_skeletonize(root, edits, ext, file_uri, source_code, source_map)
        
        source_bytes = bytearray(source_code.encode("utf-8"))
        for start_byte, end_byte, replacement in sorted(edits, key=lambda x: x[0], reverse=True):
            source_bytes[start_byte:end_byte] = replacement.encode("utf-8")
        
        distilled = source_bytes.decode("utf-8")
        final_output = distilled if skip_alignment else self._apply_hysteresis(distilled)
        return final_output, source_map

    def pack_skeletons(self, file_content_map, block_size=4096, slack=64):
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

    def _apply_hysteresis(self, text, block_size=4096, slack=64):
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

    def _find_blocks_to_skeletonize(self, node, edits, ext, file_uri, source_code, source_map):
        func_types = ("function_definition", "function_declaration", "method_definition", "arrow_function", "generator_function_declaration")
        if node.type in func_types:
            symbol_name = "anonymous"
            for child in node.children:
                if child.type in ("identifier", "property_identifier"):
                    symbol_name = source_code.encode("utf-8")[child.start_byte:child.end_byte].decode("utf-8")
                    break
            semantic_hint = ""
            is_hot = False
            if self.lsp_bridge:
                res, tier, count = self.lsp_bridge.query_definition(file_uri, node.start_point[0], node.start_point[1])
                if tier in ("L1", "L2") and res:
                    is_hot = count > 5
                    hot_tag = " [HOT_SYMBOL]" if is_hot else ""
                    semantic_hint = f" # [SEMANTIC_{tier}]{hot_tag}"
            body_node = None
            for child in node.children:
                if child.type in ("block", "statement_block"):
                    body_node = child
                    break
            if body_node:
                source_map.append({
                    "symbol": symbol_name,
                    "original_start": body_node.start_byte,
                    "original_end": body_node.end_byte,
                    "type": node.type,
                    "file_size_at_distill": len(source_code.encode("utf-8"))
                })
                if is_hot:
                    body_text = source_code.encode("utf-8")[body_node.start_byte:body_node.end_byte].decode("utf-8")
                    body_lines = body_text.splitlines()
                    preserved_count = min(len(body_lines), 10)
                    preserved_body = "\n".join(body_lines[:preserved_count]) + "\n        ... (semantic truncation)"
                    replacement = f" {preserved_body}"
                else:
                    replacement = f" pass{semantic_hint}" if ext == ".py" else f" ...{semantic_hint}"
                edits.append((body_node.start_byte, body_node.end_byte, replacement))
                return
        for child in node.children:
            self._find_blocks_to_skeletonize(child, edits, ext, file_uri, source_code, source_map)

    def stop(self):
        if self.lsp_bridge:
            self.lsp_bridge.stop()

if __name__ == "__main__":
    distiller = GCSDistiller()
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as f:
            print(distiller.skeletonize(sys.argv[1], f.read()))
