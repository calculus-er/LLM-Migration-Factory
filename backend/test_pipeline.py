"""Upload + monitor + print detailed results in one script."""
import urllib.request, json, time, sys, os

# Fix print encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BACKEND = 'http://localhost:8000'
SAMPLE  = r'C:\Users\rishu\Desktop\ECell_Hackathon\LLM-Migration-Factory\sample_test_app.py'

# 1. Upload
import urllib.parse
boundary = '----FormBoundary7MA4YWxkTrZu0gW'
with open(SAMPLE, 'rb') as f:
    file_data = f.read()

body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="sample_test_app.py"\r\n'
    f'Content-Type: text/x-python\r\n\r\n'
).encode() + file_data + f'\r\n--{boundary}--\r\n'.encode()

req = urllib.request.Request(
    f'{BACKEND}/api/upload',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
    method='POST',
)
with urllib.request.urlopen(req) as resp:
    upload = json.loads(resp.read().decode())
job_id = upload['job_id']
print(f'Uploaded. Job: {job_id}', flush=True)

# 2. Poll until done
while True:
    time.sleep(5)
    try:
        with urllib.request.urlopen(f'{BACKEND}/api/jobs/{job_id}') as resp:
            job = json.loads(resp.read().decode())
        phase = job.get('phase')
        print(f'  phase={phase}', flush=True)
        if phase in ('complete', 'failed'):
            break
    except Exception as e:
        print(f'  waiting ({e})', flush=True)

# 3. Print results
print(f'\n{"="*60}')
print(f'Phase: {job.get("phase")}  |  Error: {job.get("error")}')

r = job.get('report')
if r:
    print(f'Avg Score: {r.get("avg_semantic_score")}%')
    print(f'Cost Savings: {r.get("cost_savings_pct")}%')
    for site in r.get('optimization_results', []):
        print(f'\n{"="*60}')
        print(f'CALL SITE LINE {site.get("call_site_lineno")} — Final Score: {site.get("final_score")}')
        print(f'{"="*60}')
        for it in site.get('iterations', []):
            print(f'\n--- Iter {it["iteration"]} (Score: {it["score"]}) ---')
            print(f'SYS:  {it.get("translated_system_prompt","")[:250]}')
            print(f'USER: {it.get("translated_user_prompt","")[:250]}')
            resp_text = it.get("target_response","")
            print(f'RESP: {resp_text[:300]}')
            fb = it.get('judge_feedback', '').replace('\n', ' ')
            print(f'JUDGE: {fb[:300]}')
else:
    print('No report. Logs:')
    for l in job.get('logs', []):
        if l.get('level') in ('error', 'warn'):
            print(f'  [{l["level"]}] {l["message"]}')
