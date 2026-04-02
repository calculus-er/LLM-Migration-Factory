import urllib.request, json, time, sys
sys.stdout.reconfigure(encoding='utf-8')

BACKEND = 'http://localhost:8000'
SAMPLE = r'C:\Users\rishu\Desktop\ECell_Hackathon\LLM-Migration-Factory\sample_test2.py'

boundary = '----FormBoundary7MA4'
with open(SAMPLE, 'rb') as f:
    file_data = f.read()

body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="sample_test2.py"\r\nContent-Type: text/x-python\r\n\r\n').encode() + file_data + f'\r\n--{boundary}--\r\n'.encode()

req = urllib.request.Request(f'{BACKEND}/api/upload', data=body, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}, method='POST')
with urllib.request.urlopen(req) as resp:
    job_id = json.loads(resp.read().decode())['job_id']
print(f'Uploaded. Job: {job_id}', flush=True)

while True:
    time.sleep(2)
    with urllib.request.urlopen(f'{BACKEND}/api/jobs/{job_id}') as resp:
        job = json.loads(resp.read().decode())
    if job.get('phase') in ('complete', 'failed'):
        break

print(f'\nPhase: {job.get("phase")} | Error: {job.get("error")}')
r = job.get('report')
if r:
    for idx, site in enumerate(r.get('optimization_results', [])):
        print(f"\nGOLDEN RESPONSE: {r['golden_responses'][idx]['response_text']}")
        print(f"\nTARGET RESPONSE: {site['target_response']}")
        print(f"\nJUDGE FEEDBACK: {site['iterations'][-1]['judge_feedback']}")
else:
    for l in job.get('logs', []):
        print(f"[{l['level']}] {l['message']}")
