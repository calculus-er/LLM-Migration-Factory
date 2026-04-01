import ast
from typing import List, Dict, Any, Optional

class CallSite:
    def __init__(self, lineno: int, raw_snippet: str, args: Dict[str, Any]):
        self.lineno = lineno
        self.raw_snippet = raw_snippet
        self.args = args # type, messages, model, temperature etc.

    def __repr__(self):
        return f"CallSite(lineno={self.lineno}, model='{self.args.get('model')}')"

class OpenAIAstVisitor(ast.NodeVisitor):
    """
    Visits the Abstract Syntax Tree of a Python script to locate
    `client.chat.completions.create` or `openai.chat.completions.create`
    """
    def __init__(self, source_code: str):
        self.calls: List[CallSite] = []
        self.source_code = source_code
        self.source_lines = source_code.splitlines()
        
    def _get_snippet(self, node: ast.Call) -> str:
        # Simplistic snippet extraction
        start = node.lineno - 1
        end = node.end_lineno
        return "\n".join(self.source_lines[start:end])

    def _extract_value(self, node) -> Any:
        """Extract a Python value from an AST node, with fallbacks for complex expressions."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.JoinedStr):
            # f-string: reconstruct a representative string from its parts
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant):
                    parts.append(str(v.value))
                elif isinstance(v, ast.FormattedValue):
                    # Use the variable name or a placeholder
                    if isinstance(v.value, ast.Name):
                        parts.append(f"{{{v.value.id}}}")
                    else:
                        parts.append("{...}")
            return "".join(parts)
        elif isinstance(node, ast.Name):
            return f"{{{node.id}}}"
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            # String concatenation like "Summarize: " + text
            left = self._extract_value(node.left)
            right = self._extract_value(node.right)
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            return str(left) + str(right)
        else:
            # Last resort: try to unparse it back to source
            try:
                return ast.unparse(node)
            except Exception:
                return "(dynamic expression)"

    def _extract_dict_from_list(self, list_node: ast.List) -> List[Dict]:
        """Extracts messages from the list of dicts"""
        messages = []
        for elem in list_node.elts:
            if isinstance(elem, ast.Dict):
                msg = {}
                for k, v in zip(elem.keys, elem.values):
                    if isinstance(k, ast.Constant):
                        msg[k.value] = self._extract_value(v)
                messages.append(msg)
        return messages

    def visit_Call(self, node):
        # We are looking for something that resolves to `.chat.completions.create`
        # This is represented by successive ast.Attribute nodes: node.func is an Attribute
        
        is_openai_call = False
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'create':
                if isinstance(node.func.value, ast.Attribute) and node.func.value.attr == 'completions':
                    if isinstance(node.func.value.value, ast.Attribute) and node.func.value.value.attr == 'chat':
                        # It's `.chat.completions.create`
                        is_openai_call = True
        
        if is_openai_call:
            extracted_args = {}
            # Parse kwargs
            for keyword in node.keywords:
                key = keyword.arg
                if isinstance(keyword.value, ast.Constant):
                    extracted_args[key] = keyword.value.value
                elif isinstance(keyword.value, ast.List) and key == 'messages':
                    extracted_args['messages'] = self._extract_dict_from_list(keyword.value)
            
            snippet = self._get_snippet(node)
            site = CallSite(lineno=node.lineno, raw_snippet=snippet, args=extracted_args)
            self.calls.append(site)
            
        self.generic_visit(node)

def parse_openai_calls(source_code: str) -> List[CallSite]:
    tree = ast.parse(source_code)
    visitor = OpenAIAstVisitor(source_code)
    visitor.visit(tree)
    return visitor.calls

if __name__ == "__main__":
    # Test script run
    import sys
    import os
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        with open(sys.argv[1], 'r') as f:
            code = f.read()
            calls = parse_openai_calls(code)
            for c in calls:
                print(f"Found Call at line {c.lineno}")
                print(f"Args: {c.args}")
                print("----------")
 
