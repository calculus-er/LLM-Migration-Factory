"""
Prompt Translator — Rewrites source prompts to be optimized for
the target model using the Optimizer LLM.
Accepts optional judge feedback to iteratively improve the translation.
"""
import re
import time
from openai import OpenAI
from config import config


TRANSLATION_PROMPT = """You are an expert prompt engineer. Your task is to rewrite a prompt that was originally designed for one LLM so that it works optimally on a different model.

## ORIGINAL SYSTEM PROMPT:
---
{system_prompt}
---

## ORIGINAL USER PROMPT:
---
{user_prompt}
---

## GOLDEN RESPONSE (what the original model produced — your rewritten prompt should produce a similar response):
---
{golden_response}
---

## Instructions:
- Preserve the exact intent, output format requirements, and constraints of the original prompts.
- Adapt the language to be more explicit and structured.
- If the user prompt contains placeholder variables like {{text}} or {{variable}}, keep them exactly as-is in your rewrite.
- If the original prompt expects JSON output, make sure your rewritten prompt explicitly instructs the model to output valid JSON.
- Keep the same level of detail and specificity.
- Your goal: when the target model receives your rewritten prompts, it should produce output as close as possible to the GOLDEN RESPONSE.

## Your Response (STRICT FORMAT):
SYSTEM_PROMPT: <rewritten system prompt — single block, may span multiple lines>
USER_PROMPT: <rewritten user prompt — single block, may span multiple lines, keep all content>
"""


REFINEMENT_PROMPT = """You are an expert prompt engineer. A previous rewrite was judged and found lacking. Improve it based on the judge's feedback.

## ORIGINAL SYSTEM PROMPT (for reference):
---
{system_prompt}
---

## ORIGINAL USER PROMPT (for reference):
---
{user_prompt}
---

## GOLDEN RESPONSE (what the original model produced — aim to match this):
---
{golden_response}
---

## PREVIOUS REWRITTEN SYSTEM PROMPT:
---
{prev_system}
---

## PREVIOUS REWRITTEN USER PROMPT:
---
{prev_user}
---

## TARGET MODEL'S RESPONSE WITH PREVIOUS PROMPTS:
---
{target_response}
---

## JUDGE FEEDBACK (score: {score}/100):
{feedback}

## Instructions:
- Compare the TARGET MODEL'S RESPONSE with the GOLDEN RESPONSE above.
- Fix the specific issues mentioned in the judge's feedback.
- Make the prompts more explicit about the expected output format and style to better match the golden response.
- Keep all other aspects that were working well.

## Your Response (STRICT FORMAT):
SYSTEM_PROMPT: <improved system prompt>
USER_PROMPT: <improved user prompt with full content>
"""


def _parse_translation(raw_text: str) -> dict:
    """Parse the SYSTEM_PROMPT / USER_PROMPT response format.
    Handles reasoning model outputs that may include <think> blocks."""

    # Strip <think>...</think> blocks from reasoning models
    cleaned = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()

    system_prompt = ""
    user_prompt = ""

    # Multiline-safe regex: SYSTEM runs until USER_PROMPT; USER is rest of string
    m_sys = re.search(
        r'(?:^|\n)\s*\*{0,2}\s*SYSTEM_PROMPT\s*:\s*(.*?)(?=\n\s*\*{0,2}\s*USER_PROMPT\s*:|\Z)',
        cleaned,
        re.DOTALL | re.IGNORECASE,
    )
    m_user = re.search(
        r'(?:^|\n)\s*\*{0,2}\s*USER_PROMPT\s*:\s*(.*)\Z',
        cleaned,
        re.DOTALL | re.IGNORECASE,
    )

    if m_sys:
        system_prompt = m_sys.group(1).strip()
    if m_user:
        user_prompt = m_user.group(1).strip()

    # Fallback: simple line-by-line parse
    if not system_prompt and not user_prompt:
        for line in cleaned.splitlines():
            stripped = line.strip()
            stripped_clean = re.sub(r'\*{1,2}', '', stripped)
            if stripped_clean.upper().startswith("SYSTEM_PROMPT:"):
                system_prompt = stripped_clean.split(":", 1)[1].strip()
            elif stripped_clean.upper().startswith("USER_PROMPT:"):
                user_prompt = stripped_clean.split(":", 1)[1].strip()

    return {"system_prompt": system_prompt, "user_prompt": user_prompt}


def translate_prompt(
    system_prompt: str,
    user_prompt: str,
    golden_response: str = "",
    prev_system: str = "",
    prev_user: str = "",
    prev_target_response: str = "",
    feedback: str = "",
    score: int = 0,
) -> dict:
    """
    Translates/refines prompts using the Optimizer model via OpenAI-compatible API.
    
    Now receives the golden_response and prev_target_response so the optimizer
    can see what it's trying to match and where the previous attempt fell short.
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
            golden_response=golden_response or "(not available)",
            prev_system=prev_system,
            prev_user=prev_user,
            target_response=prev_target_response or "(not available)",
            score=score,
            feedback=feedback,
        )
    else:
        prompt = TRANSLATION_PROMPT.format(
            system_prompt=system_prompt or "(none)",
            user_prompt=user_prompt or "(none)",
            golden_response=golden_response or "(not available)",
        )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a precise prompt engineering assistant. Respond with ONLY the SYSTEM_PROMPT and USER_PROMPT blocks. No explanations, no thinking tags, no markdown formatting."},
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
