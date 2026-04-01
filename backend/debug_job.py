import sys
import json
sys.path.insert(0, r'C:\Users\rishu\Desktop\ECell_Hackathon\LLM-Migration-Factory\backend')
from pipeline.orchestrator import run_pipeline
from job_store import job_store
import time
job_id = 'test-job-' + str(int(time.time()))
job_store.create_job(job_id, r'sample_test_app.py')
with open(r'C:\Users\rishu\Desktop\ECell_Hackathon\LLM-Migration-Factory\sample_test_app.py', 'r') as f:
    code = f.read()

run_pipeline(job_id, "sample_test_app.py", code)

job = job_store.jobs[job_id]
for g in job.golden_baselines:
    print("GOLDEN LINE", g.call_site_lineno, repr(g.response_text))
