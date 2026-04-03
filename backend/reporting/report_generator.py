"""
Report Generator — Assembles the final MigrationReport with
aggregated metrics (estimated costs; tune TARGET_COST_* in config / .env).
"""
from typing import List
from models import MigrationReport, GoldenResponse, OptimizationResult
from config import config
from utils.placeholder_resolver import substitute_messages, substitute_placeholders


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

        # Estimate target cost from golden token counts using configured $/1k (rough)
        for g in golden_responses:
            input_cost = (g.prompt_tokens / 1000.0) * config.TARGET_COST_INPUT_PER_1K
            output_cost = (g.completion_tokens / 1000.0) * config.TARGET_COST_OUTPUT_PER_1K
            target_cost += input_cost + output_cost

    # Calculate savings
    cost_savings_pct = 0.0
    if original_cost > 0:
        cost_savings_pct = ((original_cost - target_cost) / original_cost) * 100.0

    # Ensure all report output substitutes variables so the UI prints actual contents 
    # instead of "{variables}". Code surgeon has ALREADY run, so this only affects the UI.
    ui_golden = []
    for g in golden_responses:
        d = g.dict()
        d['original_messages'] = substitute_messages(g.original_messages)
        ui_golden.append(GoldenResponse(**d))
        
    ui_opt = []
    for r in optimization_results:
        d = r.dict()
        d['final_system_prompt'] = substitute_placeholders(r.final_system_prompt)
        d['final_user_prompt'] = substitute_placeholders(r.final_user_prompt)
        for it in d['iterations']:
            it['translated_system_prompt'] = substitute_placeholders(it['translated_system_prompt'])
            it['translated_user_prompt'] = substitute_placeholders(it['translated_user_prompt'])
        ui_opt.append(OptimizationResult(**d))

    return MigrationReport(
        job_id=job_id,
        filename=filename,
        total_call_sites=total_call_sites,
        golden_responses=ui_golden,
        optimization_results=ui_opt,
        avg_semantic_score=round(avg_score, 2),
        original_cost_usd=round(original_cost, 6),
        target_cost_usd=round(target_cost, 6),
        cost_savings_pct=round(cost_savings_pct, 1),
        avg_original_latency_ms=round(avg_original_latency, 2),
        avg_target_latency_ms=round(avg_target_latency, 2),
        refactored_code=refactored_code,
    )
