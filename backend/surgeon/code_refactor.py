"""
Code Surgeon — AST-based source code rewriter.

Takes a Python source file that uses the OpenAI SDK and rewrites it to use
the NVIDIA NIM API (OpenAI-compatible endpoint) with the optimized prompts
from the optimization loop.
"""
import ast
import os
import textwrap
from typing import List, Dict


def refactor_code(
    original_source: str,
    optimized_prompts: List[Dict],
) -> str:
    """
    Rewrites the original Python source to use NVIDIA Llama instead of OpenAI.

    Args:
        original_source: The raw Python source code string.
        optimized_prompts: List of dicts, each with keys:
            - call_site_lineno: int
            - final_system_prompt: str
            - final_user_prompt: str

    Returns:
        The refactored Python source code as a string.
    """
    # Build a lookup: lineno -> optimized prompt data
    prompt_lookup = {p["call_site_lineno"]: p for p in optimized_prompts}

    lines = original_source.splitlines()
    tree = ast.parse(original_source)

    # Collect all edits as (start_line, end_line, replacement_text) tuples
    edits = []

    # Track if we found OpenAI imports to replace
    import_edits = []

    for node in ast.walk(tree):
        # Replace imports: `from openai import OpenAI` or `import openai`
        if isinstance(node, ast.ImportFrom) and node.module and "openai" in node.module:
            import_edits.append((node.lineno, node.end_lineno or node.lineno))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if "openai" in alias.name:
                    import_edits.append((node.lineno, node.end_lineno or node.lineno))

        # Replace client construction: `client = OpenAI(...)` or `OpenAI(...)`
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Call):
                func = node.value.func
                if isinstance(func, ast.Name) and func.id == "OpenAI":
                    indent = _get_indent(lines[node.lineno - 1])
                    nvidia_base_url = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
                    replacement = (
                        f'{indent}# NVIDIA NIM API Client (migrated from OpenAI)\n'
                        f'{indent}{ast.get_source_segment(original_source, node.targets[0])} = OpenAI(\n'
                        f'{indent}    api_key=os.environ.get("NVIDIA_API_KEY"),\n'
                        f'{indent}    base_url="{nvidia_base_url}",\n'
                        f'{indent})'
                    )
                    edits.append((node.lineno, node.end_lineno or node.lineno, replacement))

        # Replace chat.completions.create() calls
        if isinstance(node, ast.Call):
            if _is_completions_create(node):
                if node.lineno in prompt_lookup:
                    optimized = prompt_lookup[node.lineno]
                    indent = _get_indent(lines[node.lineno - 1])
                    nvidia_model = os.environ.get("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")

                    sys_prompt = optimized["final_system_prompt"].replace('"', '\\"')
                    usr_prompt = optimized["final_user_prompt"].replace('"', '\\"')

                    # Build the replacement call
                    replacement = (
                        f'{indent}# Optimized for NVIDIA Llama (migrated by LLM Migration Factory)\n'
                        f'{indent}{_get_call_target(node, original_source)}.chat.completions.create(\n'
                        f'{indent}    model="{nvidia_model}",\n'
                        f'{indent}    messages=[\n'
                        f'{indent}        {{"role": "system", "content": "{sys_prompt}"}},\n'
                        f'{indent}        {{"role": "user", "content": "{usr_prompt}"}},\n'
                        f'{indent}    ],\n'
                        f'{indent}    temperature=0.7,\n'
                        f'{indent}    max_tokens=1024,\n'
                        f'{indent})'
                    )
                    edits.append((node.lineno, node.end_lineno or node.lineno, replacement))

    # Replace import lines
    if import_edits:
        # We'll replace the first import and remove any others
        first_import = import_edits[0]
        import_replacement = (
            'import os\n'
            'from openai import OpenAI  # Using OpenAI-compatible client for NVIDIA NIM'
        )
        edits.append((first_import[0], first_import[1], import_replacement))
        # Mark remaining imports for deletion
        for imp in import_edits[1:]:
            edits.append((imp[0], imp[1], ""))

    # Apply edits in reverse line order to maintain correct line numbers
    edits.sort(key=lambda e: e[0], reverse=True)

    result_lines = lines[:]
    for start, end, replacement in edits:
        if replacement:
            result_lines[start - 1:end] = replacement.splitlines()
        else:
            # Delete lines
            del result_lines[start - 1:end]

    # Add a header comment
    header = (
        "# ============================================\n"
        "# Refactored by LLM Migration Factory\n"
        "# Original: OpenAI GPT → Target: NVIDIA Llama\n"
        "# ============================================\n"
    )

    return header + "\n".join(result_lines) + "\n"


def _get_indent(line: str) -> str:
    """Extract the leading whitespace from a line."""
    return line[:len(line) - len(line.lstrip())]


def _is_completions_create(node: ast.Call) -> bool:
    """Check if the call node is `*.chat.completions.create()`."""
    if isinstance(node.func, ast.Attribute) and node.func.attr == "create":
        val = node.func.value
        if isinstance(val, ast.Attribute) and val.attr == "completions":
            val2 = val.value
            if isinstance(val2, ast.Attribute) and val2.attr == "chat":
                return True
    return False


def _get_call_target(node: ast.Call, source: str) -> str:
    """Extract the variable name before `.chat.completions.create()`."""
    # Walk down to find the root Name node
    current = node.func
    while isinstance(current, ast.Attribute):
        current = current.value
    if isinstance(current, ast.Name):
        return current.id
    return "client"
