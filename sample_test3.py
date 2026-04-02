import os
import sqlite3
import json
import openai
from fastapi import FastAPI, HTTPException, Request
from datetime import datetime

# --- DIRTY GLOBAL STATE & CONFIG ---
app = FastAPI()
DB_PATH = "legacy_system_v1.db"
openai.api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Initialize a legacy SQLite DB (Tight coupling to local disk)
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs 
                      (id INTEGER PRIMARY KEY, prompt TEXT, response TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- THE "MIGRATION NIGHTMARE" ENDPOINTS ---

@app.post("/v1/generate-report")
async def generate_report(request: Request):
    """
    Combines synchronous DB calls, legacy OpenAI syntax, 
    and manual JSON parsing in a single block.
    """
    data = await request.json()
    user_input = data.get("query")
    
    if not user_input:
        raise HTTPException(status_code=400, detail="Missing query")

    # Call 1: Legacy OpenAI Completion (Old Syntax)
    # This is difficult to migrate because it uses the deprecated engine/prompt structure
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Summarize this for a corporate report: {user_input}",
            max_tokens=100,
            temperature=0.5
        )
        summary = response.choices[0].text.strip()
    except Exception as e:
        return {"error": "OpenAI legacy call failed", "details": str(e)}

    # Direct DB injection (Non-async, prone to blocking)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (prompt, response, timestamp) VALUES (?, ?, ?)",
                   (user_input, summary, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    return {"status": "success", "report_id": 101, "content": summary}


@app.post("/v1/chat/analyze")
async def analyze_sentiment(request: Request):
    """
    Uses the ChatCompletion syntax but forces a specific 
    schema that is hard-coded into the logic.
    """
    body = await request.json()
    messages = body.get("messages")

    # Call 2: Standard ChatCompletion (Legacy style)
    # Hardcoded logic makes it difficult to abstract for other LLMs
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a sentiment analyzer. Return ONLY JSON."},
            {"role": "user", "content": f"Analyze: {messages}"}
        ]
    )
    
    raw_content = completion.choices[0].message.content
    
    # Brittle parsing logic
    try:
        structured_data = json.loads(raw_content)
    except:
        structured_data = {"raw": raw_content, "warning": "Failed to parse AI response"}

    return {"analysis": structured_data}


@app.get("/system/cleanup")
def heavy_cleanup():
    """
    A synchronous, blocking system call that interacts directly 
    with the OS—a nightmare for containerization/cloud migration.
    """
    try:
        # Dummy "cleanup" of temp files
        files = os.listdir("./temp_reports")
        for f in files:
            os.remove(f"./temp_reports/{f}")
        return {"message": f"Cleaned up {len(files)} files"}
    except FileNotFoundError:
        return {"message": "No directory found, skipping."}


@app.post("/v1/batch-process")
async def batch_process(request: Request):
    """
    Call 3: Using legacy Embedding calls mixed with list comprehensions.
    """
    data = await request.json()
    texts = data.get("inputs", [])

    # Legacy Embedding syntax
    response = openai.Embedding.create(
        input=texts,
        model="text-embedding-ada-002"
    )
    
    # Tightly coupled mapping logic
    embeddings = [record['embedding'] for record in response['data']]
    
    return {"vectors": embeddings, "count": len(embeddings)}

if __name__ == "__main__":
    import uvicorn
    # Hardcoded port and host
    uvicorn.run(app, host="0.0.0.0", port=8080)