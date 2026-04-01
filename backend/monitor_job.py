import urllib.request, json, sys, time

job_id = sys.argv[1] if len(sys.argv) > 1 else 'job-af2fca8e'

while True:
    try:
        with urllib.request.urlopen(f'http://localhost:8000/api/jobs/{job_id}') as resp:
            job = json.loads(resp.read().decode())
        phase = job.get('phase')
        if phase in ('complete', 'failed'):
            break
        print(f'Phase: {phase} ...', flush=True)
        time.sleep(5)
    except Exception as e:
        print(f'Waiting... ({e})', flush=True)
        time.sleep(3)

print(f'\n=== JOB {job_id} ===')
print(f'Phase: {job.get("phase")}')
print(f'Error: {job.get("error")}')

r = job.get('report')
if r:
    print(f'Avg Score: {r.get("avg_semantic_score")}%')
    print(f'Cost Savings: {r.get("cost_savings_pct")}%')
    for site in r.get('optimization_results', []):
        print(f'\n--- Call Site Line {site.get("call_site_lineno")} ---')
        print(f'Final Score: {site.get("final_score")}')
        for it in site.get('iterations', []):
            print(f'  Iter {it["iteration"]}: Score={it["score"]}')
            fb = it.get('judge_feedback', '').replace('\n', ' ')
            print(f'    Feedback: {fb[:200]}')
else:
    print('No report generated')
    for l in job.get('logs', []):
        if l.get('level') in ('error', 'warn'):
            print(f'  [{l["level"]}] {l["message"]}')
