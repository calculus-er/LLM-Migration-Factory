"""
Report Generator — Assembles the final MigrationReport with
aggregated metrics comparing original (OpenAI) vs target (NVIDIA Llama).
"""
from typing import List
from models import MigrationReport, GoldenResponse, OptimizationResult


# Rough cost estimates for NVIDIA NIM Llama per 1k tokens
NVIDIA_COST_PER_1K = {"input": 0.0003, "output": 0.0006}


def generate_report(
    job_id: str,
    filename: str,
    golden_responses: List[GoldenResponse],
    optimization_results: List[OptimizationResult],
    refactored_code: str,
) -> MigrationReport:
    """
    Compiles all pipeline results into a single MigrationReport.
    """
    total_call_sites = len(golden_responses)

    # Aggregate original costs and latencies
    original_cost = sum(g.estimated_cost_usd for g in golden_responses)
    avg_original_latency = (
        sum(g.latency_ms for g in golden_responses) / total_call_sites
        if total_call_sites > 0
        else 0.0
    )

    # Aggregate target metrics
    avg_score = 0.0
    target_cost = 0.0
    avg_target_latency = 0.0

    if optimization_results:
        scores = [r.final_score for r in optimization_results]
        avg_score = sum(scores) / len(scores)

        latencies = [r.target_latency_ms for r in optimization_results]
        avg_target_latency = sum(latencies) / len(latencies)

        # Estimate target cost from the golden token counts (rough approximation)
        for g in golden_responses:
            input_cost = (g.prompt_tokens / 1000.0) * NVIDIA_COST_PER_1K["input"]
            output_cost = (g.completion_tokens / 1000.0) * NVIDIA_COST_PER_1K["output"]
            target_cost += input_cost + output_cost

    # Calculate savings
    cost_savings_pct = 0.0
    if original_cost > 0:
        cost_savings_pct = ((original_cost - target_cost) / original_cost) * 100.0

    return MigrationReport(
        job_id=job_id,
        filename=filename,
        total_call_sites=total_call_sites,
        golden_responses=golden_responses,
        optimization_results=optimization_results,
        avg_semantic_score=round(avg_score, 2),
        original_cost_usd=round(original_cost, 6),
        target_cost_usd=round(target_cost, 6),
        cost_savings_pct=round(cost_savings_pct, 1),
        avg_original_latency_ms=round(avg_original_latency, 2),
        avg_target_latency_ms=round(avg_target_latency, 2),
        refactored_code=refactored_code,
    )
