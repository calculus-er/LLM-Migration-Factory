import urllib.request, json
try:
    with urllib.request.urlopen('http://localhost:8000/api/jobs') as resp:
        jobs = json.loads(resp.read().decode())
    latest_job_id = jobs[-1]['job_id']
    with urllib.request.urlopen(f'http://localhost:8000/api/jobs/{latest_job_id}') as resp:
        job = json.loads(resp.read().decode())
    
    print(latest_job_id)
    r = job.get('report', {})
    if r:
        print("Final Score:", r.get('avg_semantic_score'))
        for site in r.get('optimization_results', []):
            print("\n>> Call Site Line", site.get('call_site_lineno'))
            for it in site.get('iterations', []):
                print(f"  Iter {it['iteration']}: Score {it['score']}")
                fdb = it.get('judge_feedback', '').replace('\n', ' ')
                print(f"    Judge Feedback: {fdb[:200]}...")
except Exception as e:
    print(f'Error: {e}')
