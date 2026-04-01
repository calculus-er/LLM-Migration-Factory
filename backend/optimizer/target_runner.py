"""
Target Runner — Executes translated prompts against the Target Model.

When prompts contain {placeholder} variables, they are substituted with
the same sample data used in golden capture so the comparison is fair.
"""
import time
from openai import OpenAI
from config import config
from utils.placeholder_resolver import substitute_placeholders


def run_on_target(system_prompt: str, user_prompt: str) -> dict:
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

    client = OpenAI(
        api_key=config.TARGET_API_KEY,
        base_url=config.TARGET_BASE_URL,
    )

    messages = []
    if resolved_system:
        messages.append({"role": "system", "content": resolved_system})
    messages.append({"role": "user", "content": resolved_user})

    start = time.time()
    try:
        response = client.chat.completions.create(
            model=config.TARGET_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )
    except Exception as e:
        return {
            "response_text": f"[TARGET ERROR] {str(e)}",
            "latency_ms": (time.time() - start) * 1000,
            "prompt_tokens": 0,
            "completion_tokens": 0,
        }
    end = time.time()

    return {
        "response_text": response.choices[0].message.content or "",
        "latency_ms": (end - start) * 1000,
        "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
        "completion_tokens": getattr(response.usage, "completion_tokens", 0),
    }
