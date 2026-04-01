import time
import asyncio
from typing import Optional
from openai import OpenAI
from models import CallSite, GoldenResponse
from config import config

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
    """
    Executes the parsed CallSite against the Source model to capture the golden truth baseline.
    
    Returns:
        (GoldenResponse, None) on success, or (None, error_message) on failure.
    """
    # The model in the uploaded script (for cost estimation / logging only)
    original_model = call_site.model or "unknown"
    # The actual model we send to the Source provider's API
    source_model = config.SOURCE_MODEL

    if config.USE_MOCK_APIS:
        time.sleep(1.2)  # simulate network latency
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
        "model": source_model,  # Always use the configured Source model
        "messages": call_site.messages,
    }
    if call_site.temperature is not None:
        kwargs["temperature"] = call_site.temperature
    if call_site.max_tokens is not None:
        kwargs["max_tokens"] = call_site.max_tokens

    start_time = time.time()
    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as e:
        return None, f"API error: {str(e)}"
    end_time = time.time()

    latency_ms = (end_time - start_time) * 1000.0
    text_content = response.choices[0].message.content or ""
    
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    
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
