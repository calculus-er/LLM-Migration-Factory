"""
Code Surgeon — AST-based source code rewriter.

Takes a Python source file that uses the OpenAI SDK and rewrites it to use
the Target provider with the optimized prompts from the optimization loop.
"""
import ast
import json
from typing import List, Dict
from config import config


def refactor_code(
    original_source: str,
    optimized_prompts: List[Dict],
) -> str:
    """
    Rewrites the original Python source to use the specified Target model
    via an OpenAI-compatible SDK (Groq, OpenRouter, etc.).
    """
    prompt_lookup = {p["call_site_lineno"]: p for p in optimized_prompts}

    lines = original_source.splitlines()
    tree = ast.parse(original_source)

    edits = []
    import_edits = []
    client_var_name = "client"

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "openai" in node.module:
            import_edits.append((node.lineno, node.end_lineno or node.lineno))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if "openai" in alias.name:
                    import_edits.append((node.lineno, node.end_lineno or node.lineno))

        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Call):
                func = node.value.func
                if isinstance(func, ast.Name) and func.id == "OpenAI":
                    client_var_name = node.targets[0].id if isinstance(node.targets[0], ast.Name) else "client"
                    indent = _get_indent(lines[node.lineno - 1])

                    replacement = (
                        f'{indent}# LLM Factory: Client configured for {config.TARGET_PROVIDER}\n'
                        f'{indent}{client_var_name} = OpenAI(\n'
                        f'{indent}    api_key=os.environ.get("{config.TARGET_API_KEY_ENV_VAR}"),\n'
                        f'{indent}    base_url="{config.TARGET_BASE_URL}",\n'
                        f'{indent})'
                    )
                    edits.append((node.lineno, node.end_lineno or node.lineno, replacement))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_completions_create(node):
            if node.lineno in prompt_lookup:
                optimized = prompt_lookup[node.lineno]
                indent = _get_indent(lines[node.lineno - 1])
                target_model = config.TARGET_MODEL

                import re

                def _escape_for_fstring(text: str) -> str:
                    if not text:
                        return ""
                    text = text.replace('\\', '\\\\').replace('"""', '\\"\\"\\"')
                    pattern = re.compile(r'\{([A-Za-z_][A-Za-z0-9_]*)\}')
                    parts = []
                    last_end = 0
                    for match in pattern.finditer(text):
                        before = text[last_end:match.start()]
                        before = before.replace('{', '{{').replace('}', '}}')
                        parts.append(before)
                        parts.append(match.group(0))
                        last_end = match.end()
                    after = text[last_end:]
                    after = after.replace('{', '{{').replace('}', '}}')
                    parts.append(after)
                    return "".join(parts)

                sys_raw = optimized.get("final_system_prompt") or ""
                usr_raw = optimized.get("final_user_prompt") or ""
                sys_prompt = _escape_for_fstring(sys_raw)
                usr_prompt = _escape_for_fstring(usr_raw)

                messages_literal = (
                    f"[\n"
                    f'{indent}        {{"role": "system", "content": f"""{sys_prompt}"""}},\n'
                    f'{indent}        {{"role": "user", "content": f"""{usr_prompt}"""}}\n'
                    f'{indent}    ]'
                )

                call_target = _get_call_target(node, original_source)

                replacement = (
                    f'{indent}# LLM Factory: Optimized Prompt for {config.TARGET_PROVIDER}\n'
                    f'{indent}{call_target}.chat.completions.create(\n'
                    f'{indent}    model="{target_model}",\n'
                    f'{indent}    messages={messages_literal},\n'
                    f'{indent}    temperature=0.7,\n'
                    f'{indent}    max_tokens=1024,\n'
                    f'{indent})'
                )
                edits.append((node.lineno, node.end_lineno or node.lineno, replacement))

    if import_edits:
        first_import = import_edits[0]
        import_replacement = (
            'import json\n'
            'import os\n'
            f'from openai import OpenAI  # OpenAI-compatible SDK used for {config.TARGET_PROVIDER}'
        )
        edits.append((first_import[0], first_import[1], import_replacement))
        for imp in import_edits[1:]:
            edits.append((imp[0], imp[1], ""))

    edits.sort(key=lambda e: e[0], reverse=True)

    result_lines = lines[:]
    for start, end, replacement in edits:
        if replacement:
            result_lines[start - 1:end] = replacement.splitlines()
        else:
            del result_lines[start - 1:end]

    header = (
        "# ============================================\n"
        f"# Refactored by LLM Migration Factory\n"
        f"# Target Provider: {config.TARGET_PROVIDER}\n"
        f"# Target Model: {config.TARGET_MODEL}\n"
        "# ============================================\n"
    )

    return header + "\n".join(result_lines) + "\n"


def _get_indent(line: str) -> str:
    return line[:len(line) - len(line.lstrip())]

def _is_completions_create(node: ast.Call) -> bool:
    if isinstance(node.func, ast.Attribute) and node.func.attr == "create":
        val = node.func.value
        # SDK v1.0.0+ syntax: client.chat.completions.create
        if isinstance(val, ast.Attribute) and val.attr == "completions":
            val2 = val.value
            if isinstance(val2, ast.Attribute) and val2.attr == "chat":
                return True
        # Legacy SDK v0.28 syntax: openai.ChatCompletion.create, etc.
        elif isinstance(val, ast.Attribute) and val.attr in ("ChatCompletion", "Completion", "Embedding"):
            return True
    return False

def _get_call_target(node: ast.Call, source: str) -> str:
    current = node.func
    while isinstance(current, ast.Attribute):
        current = current.value
    if isinstance(current, ast.Name):
        return current.id
    return "client"
