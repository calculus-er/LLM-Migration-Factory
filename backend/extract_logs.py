import json

db_path = r'C:\Users\rishu\Desktop\ECell_Hackathon\LLM-Migration-Factory\backend\jobs_db.json'
with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

job_id, job = list(db.items())[-1]

with open(r'C:\Users\rishu\Desktop\ECell_Hackathon\LLM-Migration-Factory\backend\job_logs.txt', 'w', encoding='utf-8') as out:
    r = job.get('report', {})
    if r:
        out.write(f"Final Score: {r.get('avg_semantic_score')}\n")
        for site in r.get('optimization_results', []):
            out.write(f"\n>> Call Site Line {site.get('call_site_lineno')}\n")
            for it in site.get('iterations', []):
                out.write(f"  Iter {it['iteration']}: Score {it['score']}\n")
                fdb = it.get('judge_feedback', '').replace('\n', ' ')
                out.write(f"    Judge Feedback: {fdb[:500]}...\n")
