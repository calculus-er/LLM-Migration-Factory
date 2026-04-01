"""
Pipeline Orchestrator — Chains all layers of the Migration Factory together.

Flow:
  1. Parse the script (AST Parser)
  2. Capture golden ground truth (Source Model)
  3. Run optimization loop per call site (Optimizer + Target + Judge)
  4. Refactor the source code (Code Surgeon)
  5. Generate the migration report
"""
from typing import List

from models import CallSite, JobPhase, MigrationReport
from job_store import job_store
from parser.ast_parser import parse_openai_calls
from benchmarking.golden_capture import capture_golden_response
from optimizer.optimization_loop import run_optimization_loop
from surgeon.code_refactor import refactor_code
from reporting.report_generator import generate_report
from config import config


def run_pipeline(job_id: str, script_content: str, filename: str):
    """
    Executes the full migration pipeline for a given job.
    This runs in a background thread/task.
    """
    def log(msg: str, level: str = "info"):
        job_store.add_log(job_id, msg, level)

    try:
        # ========== PHASE 1: PARSING ==========
        job_store.set_phase(job_id, JobPhase.PARSING)
        log("🔍 Phase 1: Parsing source file for OpenAI call sites...")

        raw_calls = parse_openai_calls(script_content)

        if not raw_calls:
            log("No OpenAI call sites found in the uploaded file.", level="warn")
            job_store.set_phase(job_id, JobPhase.COMPLETE)
            return

        # Convert to Pydantic CallSite models
        call_sites: List[CallSite] = []
        for c in raw_calls:
            site = CallSite(
                lineno=c.lineno,
                model=c.args.get("model"),
                temperature=c.args.get("temperature"),
                max_tokens=c.args.get("max_tokens"),
                messages=c.args.get("messages", []),
                raw_snippet=c.raw_snippet,
            )
            call_sites.append(site)
            log(f"  Found call site at line {c.lineno}: model={c.args.get('model')}")

        log(f"✅ Parsing complete. {len(call_sites)} call site(s) found.", level="success")

        # ========== PHASE 2: GOLDEN CAPTURE ==========
        job_store.set_phase(job_id, JobPhase.GOLDEN_CAPTURE)
        log(f"🥇 Phase 2: Capturing golden baseline from Source model ({config.SOURCE_MODEL})...")

        golden_responses = []
        failed_lines: list[int] = []
        for i, site in enumerate(call_sites):
            log(f"  Capturing baseline for call site {i+1}/{len(call_sites)} (line {site.lineno})...")
            golden, error = capture_golden_response(site)
            if golden:
                golden_responses.append(golden)
                log(f"  Captured. Latency: {golden.latency_ms:.0f}ms, "
                    f"Tokens: {golden.prompt_tokens}+{golden.completion_tokens}, "
                    f"Cost: ${golden.estimated_cost_usd:.4f}")
            else:
                failed_lines.append(site.lineno)
                log(f"  Failed for call site at line {site.lineno}: {error}", level="error")

        if len(golden_responses) != len(call_sites):
            lines_str = ", ".join(str(x) for x in failed_lines) if failed_lines else "unknown"
            msg = (
                f"Golden capture failed for one or more call sites (lines: {lines_str}). "
                "All sites must succeed. Check SOURCE_API_KEY and SOURCE_BASE_URL in .env."
            )
            log(msg, level="error")
            job_store.set_error(job_id, msg)
            return

        log(f"Golden capture complete. {len(golden_responses)} baseline(s) recorded.", level="success")

        # ========== PHASE 3: OPTIMIZATION LOOP ==========
        job_store.set_phase(job_id, JobPhase.OPTIMIZING)
        log(f"🔄 Phase 3: Running agentic optimization loop...")

        optimization_results = []
        for i, (site, golden) in enumerate(zip(call_sites, golden_responses, strict=True)):
            log(f"  Optimizing call site {i+1}/{len(call_sites)} (line {site.lineno})...")
            result = run_optimization_loop(
                call_site=site,
                golden=golden,
                log_fn=log,
            )
            optimization_results.append(result)

        log(f"✅ Optimization complete for all {len(optimization_results)} call site(s).", level="success")

        # ========== PHASE 4: CODE REFACTORING ==========
        job_store.set_phase(job_id, JobPhase.REFACTORING)
        log("🔧 Phase 4: Refactoring source code (Code Surgeon)...")

        optimized_prompts = [
            {
                "call_site_lineno": r.call_site_lineno,
                "final_system_prompt": r.final_system_prompt,
                "final_user_prompt": r.final_user_prompt,
            }
            for r in optimization_results
        ]

        refactored = refactor_code(script_content, optimized_prompts)
        log(f"✅ Source code successfully refactored to use {config.TARGET_PROVIDER}!", level="success")

        # ========== PHASE 5: REPORT ==========
        log("📊 Phase 5: Generating migration report...")

        report = generate_report(
            job_id=job_id,
            filename=filename,
            golden_responses=golden_responses,
            optimization_results=optimization_results,
            refactored_code=refactored,
        )

        job_store.set_report(job_id, report)
        job_store.set_phase(job_id, JobPhase.COMPLETE)
        log(f"🎉 Migration complete! Semantic score: {report.avg_semantic_score}%, "
            f"Cost savings: {report.cost_savings_pct}%", level="success")

    except Exception as e:
        log(f"💥 Pipeline error: {str(e)}", level="error")
        job_store.set_error(job_id, str(e))
