"""
Evaluator — Uses the Judge model (via OpenAI-compatible API) to compare
the target model's response against the golden ground truth.
Returns a score (0-100) and detailed feedback.
"""
import re
import time
from openai import OpenAI
from config import config


JUDGE_PROMPT_TEMPLATE = """You are an expert AI output evaluator. Your job is to compare an ORIGINAL response from a production AI system with a NEW response from a different model, and judge how faithfully the NEW response reproduces the ORIGINAL.

## ORIGINAL RESPONSE (Golden Ground Truth):
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

## Evaluation Criteria:
1. **Semantic Accuracy** (40%): Does the NEW response convey the same meaning, facts, and conclusions?
2. **Format & Structure** (20%): Does the NEW response follow the same formatting (JSON, markdown, lists, etc.)?
3. **Tone & Style** (20%): Is the writing style, formality, and voice consistent?
4. **Completeness** (20%): Does the NEW response cover all the same points without missing information?

## Your Response (STRICT FORMAT):
You MUST respond with EXACTLY two lines in this format, nothing else:

SCORE: <integer 0-100>
FEEDBACK: <2-3 sentences explaining the score, noting specific differences or issues>
"""


def _strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks from reasoning model outputs."""
    # Strip XML-style thinking blocks (greedy)
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Also handle unclosed <think> blocks (model got cut off mid-thought)
    cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL)
    return cleaned.strip()


def _parse_score(text: str) -> tuple:
    """
    Robustly extract SCORE and FEEDBACK from judge output.
    Handles markdown bold, varied formatting, thinking blocks, etc.
    Returns (score: int, feedback: str).
    """
    # First, strip any thinking blocks
    text = _strip_thinking(text)

    score = 0
    feedback = text  # Default feedback is the full (cleaned) response

    # Strategy 1: Line-by-line scan for SCORE: pattern (handles markdown bold too)
    for line in text.splitlines():
        stripped = line.strip()
        # Remove markdown bold markers: **SCORE:** -> SCORE:
        cleaned_line = re.sub(r'\*{1,2}', '', stripped)

        if cleaned_line.upper().startswith("SCORE:"):
            score_part = cleaned_line.split(":", 1)[1].strip()
            # Extract first integer from the score part (handles "85", "85/100", "85 out of 100")
            match = re.search(r'(\d+)', score_part)
            if match:
                score = min(int(match.group(1)), 100)

        elif cleaned_line.upper().startswith("FEEDBACK:"):
            feedback = cleaned_line.split(":", 1)[1].strip()

    # Strategy 2: If Strategy 1 found score=0, do a broader regex search
    if score == 0:
        # Look for patterns like "Score: 85", "score is 85", "85/100", etc.
        patterns = [
            r'(?i)score\s*[:=]\s*(\d+)',       # "Score: 85" or "score=85"
            r'(\d+)\s*/\s*100',                 # "85/100"
            r'(?i)score\s+(?:is|of)\s+(\d+)',   # "score is 85" or "score of 85"
            r'(?i)(\d+)\s*(?:out of|\/)\s*100', # "85 out of 100"
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
    """
    Uses the Judge model to compare responses.
    """
    if config.USE_MOCK_APIS:
        time.sleep(1.5)  # simulate reasoning
        return {
            "score": 96,
            "feedback": "[Mock Judge] The response perfectly aligns with the required semantic meaning and preserves all vital constraints.",
            "passed": True
        }

    client = OpenAI(
        api_key=config.JUDGE_API_KEY,
        base_url=config.JUDGE_BASE_URL,
    )
    model_name = config.JUDGE_MODEL
    threshold = config.OPTIMIZATION_THRESHOLD

    prompt = JUDGE_PROMPT_TEMPLATE.format(
        golden_response=golden_response,
        target_response=target_response,
        system_prompt=system_prompt or "(none)",
        user_prompt=user_prompt or "(none)",
    )

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a strict, precise evaluation assistant. Respond with ONLY the SCORE and FEEDBACK lines. No explanations, no thinking, no markdown."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=1024,  # Reasoning models need more tokens for thinking chain
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
