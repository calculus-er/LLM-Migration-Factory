"""
Target Runner — Executes translated prompts against the Target Model.

Uses the OpenAI-compatible SDK to call any provider (Groq, OpenRouter, etc.).

When prompts contain {placeholder} variables, they are substituted with
the same sample data used in golden capture so the comparison is fair.
"""
import time
import sys

from config import config
from utils.placeholder_resolver import substitute_placeholders


def run_on_target(system_prompt: str, user_prompt: str, tools=None, tool_choice=None) -> dict:
    """
    Sends the translated system/user prompts to the specified Target model.
    Substitutes any remaining {placeholder} variables with sample data.
    """
    # Substitute placeholders so the target gets real data to process
    resolved_system = substitute_placeholders(system_prompt) if system_prompt else system_prompt
    resolved_user = substitute_placeholders(user_prompt)

    if config.USE_MOCK_APIS:
        time.sleep(1.0)
        return {
            "response_text": f"[Mock Mode] Successfully ran highly optimized {config.TARGET_MODEL} model response based on your newly structured constraints.",
            "latency_ms": 1000.0,
            "prompt_tokens": 58,
            "completion_tokens": 40,
        }

    return _run_on_openai_compatible(resolved_system, resolved_user, tools=tools, tool_choice=tool_choice)


def _run_on_openai_compatible(system_prompt: str, user_prompt: str, tools=None, tool_choice=None) -> dict:
    """
    Invoke the target model via OpenAI-compatible endpoint (Groq, etc.).
    """
    from openai import OpenAI

    client = OpenAI(
        api_key=config.TARGET_API_KEY,
        base_url=config.TARGET_BASE_URL,
    )

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    kwargs = {
        "model": config.TARGET_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
    }
    if tools:
        kwargs["tools"] = tools
    if tool_choice:
        kwargs["tool_choice"] = tool_choice

    start = time.time()
    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as e:
        print(f"[TARGET] Error: {e}", file=sys.stderr)
        return {
            "response_text": f"[TARGET ERROR] {str(e)}",
            "latency_ms": (time.time() - start) * 1000,
            "prompt_tokens": 0,
            "completion_tokens": 0,
        }
    end = time.time()

    message = response.choices[0].message
    text_content = message.content or ""

    # Handle tool call responses
    if hasattr(message, 'tool_calls') and message.tool_calls:
        import json as _json
        tool_calls_data = []
        for tc in message.tool_calls:
            tool_calls_data.append({
                "name": tc.function.name,
                "arguments": tc.function.arguments,
            })
        text_content = text_content or _json.dumps({"tool_calls": tool_calls_data})

    return {
        "response_text": text_content,
        "latency_ms": (end - start) * 1000,
        "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
        "completion_tokens": getattr(response.usage, "completion_tokens", 0),
    }
