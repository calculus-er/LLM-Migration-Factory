"""
Prompt Translator — Rewrites source prompts to be optimized for
the target model using the Optimizer LLM.
Accepts optional judge feedback to iteratively improve the translation.
"""
import time
from openai import OpenAI
from config import config


TRANSLATION_PROMPT = """You are an expert prompt engineer. Your task is to rewrite a prompt that was originally designed for OpenAI GPT models so that it works optimally on Meta's Llama model.

## ORIGINAL SYSTEM PROMPT:
---
{system_prompt}
---

## ORIGINAL USER PROMPT:
---
{user_prompt}
---

## Instructions:
- Preserve the exact intent, output format requirements, and constraints of the original prompts.
- Adapt the language to be more explicit and structured, as Llama models benefit from clear, directive instructions.
- If the original prompt expects JSON output, make sure your rewritten prompt explicitly instructs the model to output valid JSON.
- Keep the same level of detail and specificity.

## Your Response (STRICT FORMAT):
SYSTEM_PROMPT: <your rewritten system prompt on a single paragraph, no newlines>
USER_PROMPT: <your rewritten user prompt on a single paragraph, no newlines>
"""


REFINEMENT_PROMPT = """You are an expert prompt engineer. A previous version of a rewritten prompt was judged and found lacking. Your task is to improve it based on the judge's feedback.

## ORIGINAL SYSTEM PROMPT (for reference):
---
{system_prompt}
---

## ORIGINAL USER PROMPT (for reference):
---
{user_prompt}
---

## PREVIOUS REWRITTEN SYSTEM PROMPT:
---
{prev_system}
---

## PREVIOUS REWRITTEN USER PROMPT:
---
{prev_user}
---

## JUDGE FEEDBACK (score: {score}/100):
{feedback}

## Instructions:
- Fix the specific issues mentioned in the judge's feedback.
- Keep all other aspects that were working well.
- Be more explicit and directive where the judge found gaps.

## Your Response (STRICT FORMAT):
SYSTEM_PROMPT: <your improved system prompt on a single paragraph, no newlines>
USER_PROMPT: <your improved user prompt on a single paragraph, no newlines>
"""


def _parse_translation(raw_text: str) -> dict:
    """Parse the SYSTEM_PROMPT / USER_PROMPT response format.
    Handles reasoning model outputs that may include <think> blocks."""
    import re

    # Strip <think>...</think> blocks from reasoning models
    cleaned = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()

    system_prompt = ""
    user_prompt = ""

    for line in cleaned.splitlines():
        stripped = line.strip()
        # Remove markdown bold markers
        stripped_clean = re.sub(r'\*{1,2}', '', stripped)

        if stripped_clean.startswith("SYSTEM_PROMPT:"):
            system_prompt = stripped_clean.split(":", 1)[1].strip()
        elif stripped_clean.startswith("USER_PROMPT:"):
            user_prompt = stripped_clean.split(":", 1)[1].strip()

    return {"system_prompt": system_prompt, "user_prompt": user_prompt}


def translate_prompt(
    system_prompt: str,
    user_prompt: str,
    prev_system: str = "",
    prev_user: str = "",
    feedback: str = "",
    score: int = 0,
) -> dict:
    """
    Translates/refines prompts using the Optimizer model via OpenAI-compatible API.
    """
    if config.USE_MOCK_APIS:
        time.sleep(1.0)
        return {
            "system_prompt": f"[Mock Optimized System] You are a strict system optimized for {config.TARGET_MODEL}. Ensure highly structured output and constraint adherence.",
            "user_prompt": f"[Mock Optimized User] Analyze this strictly according to constraints: {user_prompt}"
        }

    client = OpenAI(
        api_key=config.OPTIMIZER_API_KEY,
        base_url=config.OPTIMIZER_BASE_URL,
    )
    model = config.OPTIMIZER_MODEL

    if prev_system and feedback:
        prompt = REFINEMENT_PROMPT.format(
            system_prompt=system_prompt or "(none)",
            user_prompt=user_prompt or "(none)",
            prev_system=prev_system,
            prev_user=prev_user,
            score=score,
            feedback=feedback,
        )
    else:
        prompt = TRANSLATION_PROMPT.format(
            system_prompt=system_prompt or "(none)",
            user_prompt=user_prompt or "(none)",
        )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a precise prompt engineering assistant. Respond with ONLY the SYSTEM_PROMPT and USER_PROMPT lines. No explanations, no thinking, no markdown."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        raw_text = response.choices[0].message.content or ""
    except Exception as e:
        return {
            "system_prompt": f"[TRANSLATOR ERROR] {str(e)}",
            "user_prompt": user_prompt,
        }

    result = _parse_translation(raw_text)

    if not result["system_prompt"] and not result["user_prompt"]:
        result["system_prompt"] = system_prompt or ""
        result["user_prompt"] = user_prompt or ""

    return result
