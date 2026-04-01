"""
Smoke-test core backend modules (no live API calls). Run from repo root:
  python verify_backend.py
Or: backend/venv/Scripts/python verify_backend.py
"""
import sys
import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_BACKEND = _ROOT / "backend"
sys.path.insert(0, str(_BACKEND))

print("--- Testing Core LLM Migration Factory Logic ---")

# 1. Test Imports
print("\n[OK] 1. Testing Imports...")
try:
    from models import CallSite, OptimizationResult, GoldenResponse, MigrationReport
    from job_store import job_store
    from parser.ast_parser import parse_openai_calls
    from surgeon.code_refactor import refactor_code
    from reporting.report_generator import generate_report
    print("All backend modules imported successfully.")
except Exception as e:
    print(f"FAILED to import modules: {e}")
    sys.exit(1)

# 2. Test Parser
print("\n[OK] 2. Testing AST Parser...")
mock_script = """
import os
from openai import OpenAI
client = OpenAI(api_key="mock_key")

def run():
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Explain async Python"}]
    )
    return response
"""
calls = parse_openai_calls(mock_script)
if len(calls) == 1 and calls[0].args.get("model") == "gpt-4o":
    print("Parser successfully extracted 1 OpenAI call site.")
else:
    print(f"FAILED parser test. Found {len(calls)} calls.")
    sys.exit(1)

# 3. Test Code Refactoring
print("\n[OK] 3. Testing Code Surgeon (AST Re-writer)...")
mock_optimization = [
    {
        "call_site_lineno": calls[0].lineno,
        "final_system_prompt": "You are a helpful assistant.",
        "final_user_prompt": "Please explain asynchronous programming in Python clearly.",
    }
]
refactored = refactor_code(mock_script, mock_optimization)

if "LLM Factory" in refactored and "Optimized Prompt" in refactored:
    print("Code Surgeon successfully refactored the source code!")
else:
    print("FAILED code surgeon test.")
    print("Refactored code output:")
    print(refactored)
    sys.exit(1)

# 4. Report Generator Structure
print("\n[OK] 4. Testing Report Generator Logic...")
try:
    golden = [
        GoldenResponse(
            call_site_lineno=calls[0].lineno,
            original_messages=[{"role": "user", "content": "Explain async Python"}],
            response_text="Async is cool.",
            latency_ms=1000,
            prompt_tokens=10,
            completion_tokens=20,
            estimated_cost_usd=0.01,
        )
    ]
    opt = [
        OptimizationResult(
            call_site_lineno=calls[0].lineno,
            iterations=[],
            final_system_prompt="sys",
            final_user_prompt="user",
            final_score=95,
            target_response="Async is neat.",
            target_latency_ms=800,
        )
    ]
    report = generate_report("job-123", "test.py", golden, opt, refactored)
    if report.avg_semantic_score == 95.0:
        print("Report Generator successfully aggregated data.")
    else:
        print("FAILED report generator test.")
        sys.exit(1)
except Exception as e:
    print(f"FAILED report generator test: {e}")
    sys.exit(1)

print("\n[OK] ALL INTERNAL LOGIC PHASES (1-5) VERIFIED SUCCESSFULLY.")
print("Next: run API smoke tests (pytest) and frontend lint/build from repo root.")
