import os
import time
from typing import Optional
from openai import OpenAI
from models import CallSite, GoldenResponse

# Simple cost estimation mapping for OpenAI tokens (per 1k tokens)
# Values might need adjusting depending on exact models used.
COST_PER_1K_TOKENS = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "default": {"input": 0.005, "output": 0.015}
}

def estimate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    rates = COST_PER_1K_TOKENS.get(model_name, COST_PER_1K_TOKENS["default"])
    input_cost = (prompt_tokens / 1000.0) * rates["input"]
    output_cost = (completion_tokens / 1000.0) * rates["output"]
    return input_cost + output_cost

def capture_golden_response(call_site: CallSite) -> Optional[GoldenResponse]:
    """
    Executes the parsed CallSite against OpenAI to capture the golden truth benchmark.
    Requires OPENAI_API_KEY environment variable.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-..."):
        print("Warning: Missing or invalid OPENAI_API_KEY")
        return None

    client = OpenAI(api_key=api_key)

    # Reconstruct kwargs exactly as they were in the original CallSite
    kwargs = {
        "model": call_site.model or "gpt-3.5-turbo",
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
        print(f"Error capturing golden response for call site on line {call_site.lineno}: {e}")
        return None
    end_time = time.time()

    latency_ms = (end_time - start_time) * 1000.0
    text_content = response.choices[0].message.content or ""
    
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    
    # Calculate estimated cost
    est_cost = estimate_cost(kwargs["model"], prompt_tokens, completion_tokens)

    return GoldenResponse(
        call_site_lineno=call_site.lineno,
        original_messages=call_site.messages,
        response_text=text_content,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        estimated_cost_usd=est_cost
    )
