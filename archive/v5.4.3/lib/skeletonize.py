import ast
import os
import re
import sys
import hashlib
from datetime import datetime
try:
    from sanitizers import sanitize_content
except ImportError:
    # Fallback if execution environment differs
    import sys
    sys.path.append(os.path.dirname(__file__))
    try:
        from sanitizers import sanitize_content
    except ImportError:
        def sanitize_content(t): return t

class PythonSkeletonizer(ast.NodeVisitor):
    def __init__(self):
        self.output = []
        self.depth = 0
        self.max_depth = 2

    def get_docstring(self, node):
        doc = ast.get_docstring(node)
        if doc:
            # Extract first paragraph (up to double newline)
            paragraphs = doc.strip().split('\n\n')
            return f'    """ {paragraphs[0]} """\n'
        return ""

    def visit_ClassDef(self, node):
        if self.depth >= self.max_depth: return
        
        decorators = [f"@{ast.unparse(d)}" for d in node.decorator_list]
        header = f"{node.name}"
        bases = [ast.unparse(b) for b in node.bases]
        if bases:
            header += f"({', '.join(bases)})"
            
        indent = "    " * self.depth
        for d in decorators:
            self.output.append(f"{indent}{d}")
        self.output.append(f"{indent}class {header}:")
        
        doc = self.get_docstring(node)
        if doc: self.output.append(f"{indent}{doc}")
        
        self.depth += 1
        self.generic_visit(node)
        self.depth -= 1

    def visit_FunctionDef(self, node):
        if self.depth >= self.max_depth: return
        self._visit_func(node)

    def visit_AsyncFunctionDef(self, node):
        if self.depth >= self.max_depth: return
        self._visit_func(node, is_async=True)

    def _visit_func(self, node, is_async=False):
        decorators = [f"@{ast.unparse(d)}" for d in node.decorator_list]
        prefix = "async " if is_async else ""
        
        # Use a more robust signature extraction for complex types
        args = ast.unparse(node.args)
        returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
        
        indent = "    " * self.depth
        for d in decorators:
            self.output.append(f"{indent}{d}")
        
        sig = f"{indent}{prefix}def {node.name}({args}){returns}:"
        self.output.append(sig)
        
        doc = self.get_docstring(node)
        if doc: self.output.append(f"{indent}{doc}")
        self.output.append(f"{indent}    ...")

def skeletonize_python(content):
    try:
        tree = ast.parse(content)
        visitor = PythonSkeletonizer()
        
        # Capture imports at top level
        imports = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(ast.unparse(node))
        
        visitor.visit(tree)
        return "\n".join(imports + [""] + visitor.output)
    except Exception as e:
        return f"# [Error parsing Python AST: {e}]\n{content[:500]}..."

def skeletonize_js_ts(content):
    """
    Lightweight signature extraction for JS/TS using regex.
    """
    lines = content.split('\n')
    output = []
    # Capture imports
    for line in lines:
        if line.strip().startswith(('import ', 'from ')):
            output.append(line.strip())
            
    output.append("")
    
    # Regex for class/function signatures (covers most standard cases)
    sig_pattern = re.compile(r'^(export\s+)?(class|async\s+function|function|interface|type)\s+([a-zA-Z0-9_$]+)')
    
    for line in lines:
        stripped = line.strip()
        if sig_pattern.search(stripped):
            output.append(stripped + " { /* ... */ }")
            
    return "\n".join(output)

def process_file(file_path):
    if not os.path.exists(file_path):
        return f"# Error: File {file_path} not found"
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"# Error reading {file_path}: {e}"
    
    mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
    sha256 = hashlib.sha256(content.encode()).hexdigest()
    
    ext = os.path.splitext(file_path)[1]
    if ext == '.py':
        skeleton = skeletonize_python(content)
        lang = "python"
    elif ext in ['.js', '.ts', '.tsx']:
        skeleton = skeletonize_js_ts(content)
        lang = "typescript"
    else:
        skeleton = f"# [Unsupported extension {ext}]\n{content[:200]}..."
        lang = "text"
        
    sanitized = sanitize_content(skeleton)
    
    header = f"#### 📄 {os.path.basename(file_path)}\n"
    header += f"- **Last Modified**: `{mtime}`\n"
    header += f"- **SHA-256 Checksum**: `{sha256}`\n"
    
    return f"{header}\n```{lang}\n{sanitized}\n```"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(process_file(sys.argv[1]))
