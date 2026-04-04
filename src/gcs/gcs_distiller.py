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

    def skeletonize(self, file_path, source_code):
        _, ext = os.path.splitext(file_path)
        parser = self.parsers.get(ext)
        if not parser:
            return self._apply_hysteresis(source_code)

        tree = parser.parse(source_code.encode("utf-8"))
        root = tree.root_node

        edits = []
        file_uri = f"file://{os.path.abspath(file_path)}"
        self._find_blocks_to_skeletonize(root, edits, ext, file_uri)
        
        source_bytes = bytearray(source_code.encode("utf-8"))
        for start_byte, end_byte, replacement in sorted(edits, key=lambda x: x[0], reverse=True):
            source_bytes[start_byte:end_byte] = replacement.encode("utf-8")
        
        distilled = source_bytes.decode("utf-8")
        return self._apply_hysteresis(distilled)

    def _apply_hysteresis(self, text, block_size=4096, slack=64):
        # Calculate size needed
        size = len(text.encode("utf-8"))
        # Hysteresis formula: (size + slack) aligned to block_size
        aligned_size = ((size + slack + block_size - 1) // block_size) * block_size
        padding_needed = aligned_size - size
        
        # Build comment template safely
        comment_header = "<!-- GCS_HYSTERESIS_PADDING_"
        comment_footer = " -->"
        min_comment_len = len(f"\n{comment_header}{padding_needed}{comment_footer}".encode("utf-8"))
        
        if padding_needed >= min_comment_len:
            padding = f"\n{comment_header}{padding_needed}{comment_footer}"
            padding += " " * (padding_needed - len(padding.encode("utf-8")))
        else:
            # If space is too tight for comment, use pure whitespace padding
            padding = " " * padding_needed

        return text + padding

    def _find_blocks_to_skeletonize(self, node, edits, ext, file_uri):
        # Target node types for body replacement (including async/generator)
        func_types = (
            "function_definition", "function_declaration", "method_definition", 
            "arrow_function", "generator_function_declaration"
        )

        if node.type in func_types:
            semantic_hint = ""
            if self.lsp_bridge:
                # Query definition as a proxy for cross-reference/hot symbol
                res, tier = self.lsp_bridge.query_definition(file_uri, node.start_point[0], node.start_point[1])
                if tier in ("L1", "L2") and res:
                    semantic_hint = f" # [SEMANTIC_{tier}]"

            body_node = None
            for child in node.children:
                if child.type in ("block", "statement_block"):
                    body_node = child
                    break

            if body_node:
                replacement = f" pass{semantic_hint}" if ext == ".py" else f" ...{semantic_hint}"
                edits.append((body_node.start_byte, body_node.end_byte, replacement))
                return # Don't recurse into function bodies

        # For classes, we keep the structure and recurse into members
        for child in node.children:
            self._find_blocks_to_skeletonize(child, edits, ext, file_uri)

    def stop(self):
        if self.lsp_bridge:
            self.lsp_bridge.stop()

if __name__ == "__main__":
    distiller = GCSDistiller()
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as f:
            print(distiller.skeletonize(sys.argv[1], f.read()))
