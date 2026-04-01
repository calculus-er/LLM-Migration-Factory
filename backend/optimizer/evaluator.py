"""
Evaluator — Uses Google Gemini as an LLM-as-a-Judge to compare
the target model's response against the golden ground truth.
Returns a score (0-100) and detailed feedback.
"""
import time
import google.generativeai as genai
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
You MUST respond with EXACTLY this format, nothing else:

SCORE: <integer 0-100>
FEEDBACK: <2-3 sentences explaining the score, noting specific differences or issues>
"""


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
        time.sleep(1.5) # simulate reasoning
        # Return a passing score to progress the loop smoothly in mock demos
        return {
            "score": 96,
            "feedback": "[Mock Judge] The response perfectly aligns with the required semantic meaning and preserves all vital constraints.",
            "passed": True
        }

    api_key = config.JUDGE_API_KEY
    model_name = config.JUDGE_MODEL
    threshold = config.OPTIMIZATION_THRESHOLD

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    prompt = JUDGE_PROMPT_TEMPLATE.format(
        golden_response=golden_response,
        target_response=target_response,
        system_prompt=system_prompt or "(none)",
        user_prompt=user_prompt or "(none)",
    )

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
    except Exception as e:
        return {
            "score": 0,
            "feedback": f"[JUDGE ERROR] {str(e)}",
            "passed": False,
        }

    score = 0
    feedback = raw_text

    for line in raw_text.splitlines():
        line_stripped = line.strip()
        if line_stripped.upper().startswith("SCORE:"):
            try:
                score_str = line_stripped.split(":", 1)[1].strip()
                score = int(score_str.split("/")[0].strip())
            except (ValueError, IndexError):
                score = 0
        elif line_stripped.upper().startswith("FEEDBACK:"):
            feedback = line_stripped.split(":", 1)[1].strip()

    return {
        "score": score,
        "feedback": feedback,
        "passed": score >= threshold,
    }
