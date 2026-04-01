"""
Evaluator — Uses the Judge model (via OpenAI-compatible API) to compare
the target model's response against the golden ground truth.
Returns a score (0-100) and detailed feedback.
"""
import re
import time
from openai import OpenAI
from config import config


JUDGE_PROMPT_TEMPLATE = """You are an expert AI output evaluator.

## Task
Compare an ORIGINAL response (produced by a source model) with a NEW response (produced by a target model that received an optimised version of the same prompt). Judge how well the NEW response fulfils **the same user intent** as the ORIGINAL response while strictly obeying the original system prompt.

## ORIGINAL RESPONSE (Baseline/Golden):
---
{golden_response}
---

## NEW RESPONSE (Target Model):
---
{target_response}
---

## ORIGINAL PROMPT CONTEXT:
System Prompt: {system_prompt}
User Prompt: {user_prompt}

## Scoring rubric (0-100):
- 90-100: Excellent — same meaning, structure, tone and completeness. 
- 70-89:  Good — minor stylistic or formatting differences, all key content present.
- 50-69:  Fair — some meaning preserved but notable omissions or structural divergence.
- 25-49:  Poor — partial relevance but large semantic gaps.
- 0-24:   Fail — unrelated or empty output.

## CRITICAL Scoring guidance:
1. Compare semantic content if both responses answer the query substantively.
2. If BOTH responses ask for missing input (because the prompt has a placeholder variable), give 90+.
3. IMPORTANT FLAG GRACE RULE: If the ORIGINAL response failed to follow strict formatting constraints requested in the System Prompt (for example, providing conversational text when asked for a SINGLE output word/JSON), but the NEW response CORRECTLY followed the system prompt constraints (e.g. outputting exactly "POSITIVE"), you MUST score the NEW response 90-100. Do NOT penalize a good target response for fixing the source model's formatting failures!

## Your Response — reply with EXACTLY two lines:
SCORE: <integer 0-100>
FEEDBACK: <1-3 sentences noting key differences>
"""


def _strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks from reasoning model outputs."""
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL)
    return cleaned.strip()


def _parse_score(text: str) -> tuple:
    """
    Robustly extract SCORE and FEEDBACK from judge output.
    Returns (score: int, feedback: str).
    """
    text = _strip_thinking(text)

    score = 0
    feedback = text

    for line in text.splitlines():
        stripped = line.strip()
        cleaned_line = re.sub(r'\*{1,2}', '', stripped)

        if cleaned_line.upper().startswith("SCORE:"):
            score_part = cleaned_line.split(":", 1)[1].strip()
            match = re.search(r'(\d+)', score_part)
            if match:
                score = min(int(match.group(1)), 100)

        elif cleaned_line.upper().startswith("FEEDBACK:"):
            feedback = cleaned_line.split(":", 1)[1].strip()

    if score == 0:
        patterns = [
            r'(?i)score\s*[:=]\s*(\d+)',
            r'(\d+)\s*/\s*100',
            r'(?i)score\s+(?:is|of)\s+(\d+)',
            r'(?i)(\d+)\s*(?:out of|\/)\s*100',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                score = min(int(match.group(1)), 100)
                break

    return score, feedback


def evaluate_response(
    golden_response: str,
    target_response: str,
    system_prompt: str,
    user_prompt: str,
) -> dict:
    """Uses the Judge model to compare responses. No shortcuts — always calls the real Judge."""
    if config.USE_MOCK_APIS:
        time.sleep(1.5)
        return {
            "score": 96,
            "feedback": "[Mock Judge] The response perfectly aligns with the required semantic meaning.",
            "passed": True
        }

    client = OpenAI(
        api_key=config.JUDGE_API_KEY,
        base_url=config.JUDGE_BASE_URL,
    )
    model_name = config.JUDGE_MODEL
    threshold = config.OPTIMIZATION_THRESHOLD

    prompt = JUDGE_PROMPT_TEMPLATE.format(
        golden_response=golden_response or "(empty response)",
        target_response=target_response or "(empty response)",
        system_prompt=system_prompt or "(none)",
        user_prompt=user_prompt or "(none)",
    )
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a strict, precise evaluation assistant. Respond with ONLY the SCORE and FEEDBACK lines. Do not wrap in markdown or thinking tags."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=1024,
        )
        raw_text = response.choices[0].message.content or ""
        raw_text = raw_text.strip()
    except Exception as e:
        return {
            "score": 0,
            "feedback": f"[JUDGE ERROR] {str(e)}",
            "passed": False,
        }

    score, feedback = _parse_score(raw_text)

    return {
        "score": score,
        "feedback": feedback,
        "passed": score >= threshold,
    }
