import time
from typing import Optional
from openai import OpenAI
from models import CallSite, GoldenResponse
from config import config
from utils.placeholder_resolver import substitute_messages, has_placeholders

COST_PER_1K_TOKENS = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "default": {"input": 0.001, "output": 0.002}
}

def estimate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    rates = COST_PER_1K_TOKENS.get(model_name, COST_PER_1K_TOKENS["default"])
    input_cost = (prompt_tokens / 1000.0) * rates["input"]
    output_cost = (completion_tokens / 1000.0) * rates["output"]
    return input_cost + output_cost

def capture_golden_response(call_site: CallSite) -> tuple:
    original_model = call_site.model or "unknown"
    source_model = config.SOURCE_MODEL

    api_messages = substitute_messages(call_site.messages)

    import sys
    print(f"[GOLDEN] Original msg: {call_site.messages}", file=sys.stderr)
    print(f"[GOLDEN] Substituted msg: {api_messages}", file=sys.stderr)

    if config.USE_MOCK_APIS:
        time.sleep(1.2)
        return GoldenResponse(
            call_site_lineno=call_site.lineno,
            original_messages=call_site.messages,
            response_text="[Mock Mode] This is a simulated original response from the Source Model.",
            latency_ms=1200.0,
            prompt_tokens=45,
            completion_tokens=30,
            estimated_cost_usd=estimate_cost(original_model, 45, 30)
        ), None

    if not config.SOURCE_API_KEY:
        return None, "Missing SOURCE_API_KEY in .env"

    client = OpenAI(
        api_key=config.SOURCE_API_KEY,
        base_url=config.SOURCE_BASE_URL,
    )

    kwargs = {
        "model": source_model,
        "messages": api_messages,
    }
    if call_site.temperature is not None:
        kwargs["temperature"] = call_site.temperature
    if call_site.max_tokens is not None:
        kwargs["max_tokens"] = call_site.max_tokens

    start_time = time.time()
    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as e:
        print(f"[GOLDEN] Error: {e}", file=sys.stderr)
        return None, f"API error: {str(e)}"
    end_time = time.time()

    latency_ms = (end_time - start_time) * 1000.0
    text_content = response.choices[0].message.content or ""
    
    print(f"[GOLDEN] Response: {repr(text_content)}", file=sys.stderr)
    
    prompt_tokens = getattr(response.usage, "prompt_tokens", 0)
    completion_tokens = getattr(response.usage, "completion_tokens", 0)
    
    est_cost = estimate_cost(original_model, prompt_tokens, completion_tokens)

    return GoldenResponse(
        call_site_lineno=call_site.lineno,
        original_messages=call_site.messages, 
        response_text=text_content,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        estimated_cost_usd=est_cost
    ), None
