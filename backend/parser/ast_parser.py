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
        self.variables: Dict[str, Any] = {}
        
    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                val = self._extract_value(node.value, ignore_unparse=True)
                if val is None:
                    val = self._extract_complex_value(node.value)
                if val is not None:
                    self.variables[target.id] = val
            elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                # Track self.model = "gpt-4o" etc.
                key = f"{target.value.id}.{target.attr}"
                val = self._extract_value(node.value, ignore_unparse=True)
                if val is None:
                    val = self._extract_complex_value(node.value)
                if val is not None:
                    self.variables[key] = val
        self.generic_visit(node)

    def _get_snippet(self, node: ast.Call) -> str:
        # Simplistic snippet extraction
        start = node.lineno - 1
        end = node.end_lineno
        return "\n".join(self.source_lines[start:end])

    def _extract_value(self, node, ignore_unparse=False) -> Any:
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
                        if v.value.id in self.variables:
                            parts.append(str(self.variables[v.value.id]))
                        else:
                            parts.append(f"{{{v.value.id}}}")
                    else:
                        parts.append("{...}")
            return "".join(parts)
        elif isinstance(node, ast.Name):
            if node.id in self.variables:
                return self.variables[node.id]
            return f"{{{node.id}}}"
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            # Resolve self.model, self.system_prompt, etc.
            key = f"{node.value.id}.{node.attr}"
            if key in self.variables:
                return self.variables[key]
            return f"{{{key}}}"
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            # String concatenation like "Summarize: " + text
            left = self._extract_value(node.left, ignore_unparse=ignore_unparse)
            right = self._extract_value(node.right, ignore_unparse=ignore_unparse)
            if left is not None and right is not None:
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                return str(left) + str(right)
            return None if ignore_unparse else "(dynamic expression)"
        else:
            # Last resort: try to unparse it back to source
            if ignore_unparse:
                return None
            try:
                return ast.unparse(node)
            except Exception:
                return "(dynamic expression)"

    def _extract_complex_value(self, node) -> Any:
        """Safely extract complex nested structures like tools definitions."""
        try:
            # Use ast.literal_eval on the unparsed source for safe evaluation
            source = ast.unparse(node)
            return ast.literal_eval(source)
        except Exception:
            return None

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
        # or legacy `openai.ChatCompletion.create` / `openai.Completion.create`
        is_openai_call = False
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'create':
                # SDK v1.0.0+ syntax: client.chat.completions.create
                if isinstance(node.func.value, ast.Attribute) and node.func.value.attr == 'completions':
                    if isinstance(node.func.value.value, ast.Attribute) and node.func.value.value.attr == 'chat':
                        is_openai_call = True
                # Legacy SDK v0.28 syntax: openai.ChatCompletion.create, etc.
                elif isinstance(node.func.value, ast.Attribute) and node.func.value.attr in ('ChatCompletion', 'Completion', 'Embedding'):
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
                elif isinstance(keyword.value, ast.List) and key == 'tools':
                    tools = self._extract_complex_value(keyword.value)
                    if tools:
                        extracted_args['tools'] = tools
                elif isinstance(keyword.value, ast.Name):
                    resolved = self._extract_value(keyword.value)
                    if resolved and not (isinstance(resolved, str) and resolved.startswith('{')):
                        extracted_args[key] = resolved
                    elif isinstance(resolved, str) and resolved.startswith('{'):
                        extracted_args[key] = resolved
                elif isinstance(keyword.value, ast.Attribute):
                    resolved = self._extract_value(keyword.value)
                    if resolved and not (isinstance(resolved, str) and resolved.startswith('{')):
                        extracted_args[key] = resolved
                elif key == 'prompt':
                    # Legacy Completion string prompt -> translate to value or placeholder
                    val = self._extract_value(keyword.value)
                    if val is not None:
                        extracted_args['prompt'] = val
                elif key == 'input':
                    # Legacy Embedding input
                    val = self._extract_value(keyword.value)
                    if val is not None:
                        extracted_args['input'] = val

            # Normalize legacy Completion/Embedding arguments to modern API model assumptions
            if 'prompt' in extracted_args and 'messages' not in extracted_args:
                extracted_args['messages'] = [{'role': 'user', 'content': extracted_args['prompt']}]
            if 'input' in extracted_args and 'messages' not in extracted_args:
                extracted_args['messages'] = [{'role': 'user', 'content': str(extracted_args['input'])}]
            if 'engine' in extracted_args and 'model' not in extracted_args:
                extracted_args['model'] = extracted_args['engine']
            
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
 
