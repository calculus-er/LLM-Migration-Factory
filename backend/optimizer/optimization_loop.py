"""
Optimization Loop — Orchestrates the full iterative cycle:
  1. Optimizer model translates the prompt
  2. Target model executes the translated prompt
  3. Judge model evaluates the result against the golden truth
  4. If score < threshold, feed feedback back to the Optimizer and retry
"""
import os
from typing import Callable, Optional

from models import CallSite, GoldenResponse, OptimizationIteration, OptimizationResult
from optimizer.prompt_translator import translate_prompt
from optimizer.target_runner import run_on_target
from optimizer.evaluator import evaluate_response
from config import config


def run_optimization_loop(
    call_site: CallSite,
    golden: GoldenResponse,
    log_fn: Optional[Callable] = None,
) -> OptimizationResult:
    """
    Runs the full translate → execute → evaluate loop for a single call site.

    Args:
        call_site: The parsed OpenAI call site
        golden: The golden ground truth response from the Source model
        log_fn: Optional callback for streaming log messages (e.g., to WebSocket)

    Returns:
        OptimizationResult with all iteration details and the final best prompt
    """
    max_iterations = config.OPTIMIZATION_MAX_ITERATIONS
    threshold = config.OPTIMIZATION_THRESHOLD

    system_prompt = call_site.system_prompt or ""
    user_prompt = call_site.user_prompt or ""

    iterations = []
    best_score = 0
    best_iteration = None

    prev_system = ""
    prev_user = ""
    prev_feedback = ""
    prev_score = 0

    def log(msg: str, level: str = "info"):
        if log_fn:
            log_fn(msg, level)

    for i in range(1, max_iterations + 1):
        log(f"Iteration {i}/{max_iterations}: Translating prompt via {config.OPTIMIZER_MODEL}...")

        # Step 1: Translate (or refine) the prompt
        translated = translate_prompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            prev_system=prev_system,
            prev_user=prev_user,
            feedback=prev_feedback,
            score=prev_score,
        )

        t_system = translated["system_prompt"]
        t_user = translated["user_prompt"]

        log(f"Iteration {i}: Running translated prompt on {config.TARGET_MODEL} target...")

        # Step 2: Execute on Target model
        target_result = run_on_target(t_system, t_user)
        target_response = target_result["response_text"]

        log(f"Iteration {i}: Target responded ({target_result['latency_ms']:.0f}ms). Sending to {config.JUDGE_MODEL} Judge...")

        # Step 3: Evaluate with Judge
        eval_result = evaluate_response(
            golden_response=golden.response_text,
            target_response=target_response,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        score = eval_result["score"]
        feedback = eval_result["feedback"]
        passed = eval_result["passed"]

        iteration = OptimizationIteration(
            iteration=i,
            translated_system_prompt=t_system,
            translated_user_prompt=t_user,
            target_response=target_response,
            score=score,
            judge_feedback=feedback,
            passed=passed,
        )
        iterations.append(iteration)

        if score > best_score:
            best_score = score
            best_iteration = iteration

        if passed:
            log(f"✅ Iteration {i}: PASSED with score {score}/100!", level="success")
            break
        else:
            log(f"⚠️ Iteration {i}: Score {score}/100 (need {threshold}). Judge: {feedback}", level="warn")

        # Feed back into the next iteration
        prev_system = t_system
        prev_user = t_user
        prev_feedback = feedback
        prev_score = score

    if not best_iteration:
        # Shouldn't happen, but safeguard
        best_iteration = iterations[-1] if iterations else None

    final = best_iteration or iterations[0]

    result = OptimizationResult(
        call_site_lineno=call_site.lineno,
        iterations=iterations,
        final_system_prompt=final.translated_system_prompt,
        final_user_prompt=final.translated_user_prompt,
        final_score=final.score,
        target_response=final.target_response,
        target_latency_ms=target_result["latency_ms"],
    )

    if final.passed:
        log(f"🎉 Optimization complete! Final score: {final.score}/100", level="success")
    else:
        log(f"⚡ Max iterations reached. Best score: {best_score}/100 (best-effort)", level="warn")

    return result
