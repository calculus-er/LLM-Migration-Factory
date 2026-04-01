import urllib.request, json, sys

job_id = sys.argv[1] if len(sys.argv) > 1 else 'job-771b3d8a'

with urllib.request.urlopen(f'http://localhost:8000/api/jobs/{job_id}') as resp:
    job = json.loads(resp.read().decode())

r = job.get('report', {})
for site in r.get('optimization_results', []):
    print(f'\n{"="*60}')
    print(f'CALL SITE LINE {site.get("call_site_lineno")}')
    print(f'Final Score: {site.get("final_score")}')
    print(f'{"="*60}')
    for it in site.get('iterations', []):
        print(f'\n--- Iteration {it["iteration"]} (Score: {it["score"]}) ---')
        print(f'System: {it.get("translated_system_prompt", "")[:200]}')
        print(f'User: {it.get("translated_user_prompt", "")[:200]}')
        print(f'Target Response: {it.get("target_response", "")[:300]}')
        fb = it.get('judge_feedback', '').replace('\n', ' ')
        print(f'Feedback: {fb[:300]}')
