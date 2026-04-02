import os
import sqlite3
import json
import base64
import hashlib
import openai
import requests
import pandas as pd # Adding a heavy data dependency for no reason
from fastapi import FastAPI, HTTPException, Request, Depends
from datetime import datetime
from functools import lru_cache

# --- CONFIGURATION (HARDCODED & BRITTLE) ---
app = FastAPI()
DB_PATH = os.path.join(os.getcwd(), "v1_legacy_storage.db")
TEMP_DIR = "/tmp/legacy_cache" # Linux-specific path, breaks on Windows
openai.api_key = os.getenv("OPENAI_KEY", "sk-legacy-key-missing-in-prod")

# Global in-memory cache that isn't thread-safe
TRANSFORM_CACHE = {}

def bootstrap():
    """Initializes disk-heavy dependencies immediately on import."""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS blob_store 
                 (key TEXT PRIMARY KEY, data TEXT, meta BLOB, created_at TIMESTAMP)''')
    conn.commit()
    conn.close()

bootstrap()

# --- UTILITY SPAGHETTI ---

def _legacy_crypto_hash(content: str):
    """Obscure custom hashing used for keys, difficult to replicate exactly elsewhere."""
    return hashlib.md5((content + "SALT_V1").encode()).hexdigest()

# --- ENDPOINTS ---

@app.post("/api/v2/complex-pipeline")
async def complex_pipeline(request: Request):
    """
    NEEDS MIGRATION: This endpoint mixes 3 different OpenAI legacy calls, 
    local disk I/O, and manual JSON schema validation.
    """
    raw_payload = await request.body()
    try:
        data = json.loads(raw_payload)
    except:
        raise HTTPException(status_code=422, detail="Malformed JSON - standard parsers might fail")

    user_query = data.get("q", "")
    
    # --- OpenAI CALL 1: Legacy Completion Engine (Pre-Chat) ---
    # Difficulty: Uses 'engine' parameter which is deprecated in newer SDKs.
    prompt_craft = f"Convert this to SQL: {user_query}"
    res1 = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt_craft,
        max_tokens=50,
        stop=["\n"]
    )
    generated_sql = res1.choices[0].text.strip()

    # --- OpenAI CALL 2: Legacy Embedding Call ---
    # Difficulty: Returns a nested dictionary structure that changed in v1.0.0+
    embed_res = openai.Embedding.create(
        input=[generated_sql],
        model="text-embedding-ada-002"
    )
    vector = embed_res['data'][0]['embedding']

    # --- DISK PERSISTENCE (Synchronous & Blocking) ---
    # This will block the entire FastAPI event loop under load.
    file_key = _legacy_crypto_hash(generated_sql)
    local_path = f"{TEMP_DIR}/{file_key}.json"
    
    with open(local_path, "w") as f:
        f.write(json.dumps({"sql": generated_sql, "vec_head": vector[:5]}))

    # --- OpenAI CALL 3: Legacy ChatCompletion with manual system-prompt injection ---
    # Difficulty: Mixing ChatCompletion with Completion logic in one flow.
    chat_res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0301", # Specifically pinned to an old snapshot
        messages=[
            {"role": "system", "content": "You are a helpful assistant that explains SQL."},
            {"role": "user", "content": f"Explain this: {generated_sql}"}
        ],
        temperature=0
    )
    explanation = chat_res.choices[0].message['content']

    # Final logic: Writing to SQLite (Manual connection management)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO blob_store VALUES (?, ?, ?, ?)", 
                   (file_key, explanation, base64.b64encode(str(vector).encode()), datetime.now()))
    conn.commit()
    conn.close()

    return {
        "id": file_key,
        "explanation": explanation,
        "metadata": {"path": local_path, "engine": "davinci-003"}
    }

@app.get("/internal/debug-dump")
def debug_dump():
    """
    Uses Pandas to read the SQLite DB and export to CSV.
    Huge overhead for a simple API.
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM blob_store", conn)
    csv_data = df.to_csv()
    conn.close()
    return {"raw_csv": csv_data}

@app.get("/health")
def health_check():
    """Tied to a specific hardware check that will fail in many cloud environments."""
    load = os.getloadavg() if hasattr(os, 'getloadavg') else (0,0,0)
    return {"status": "ok", "load": load}

# --- THE "MONSTER" BATCH PROCESSOR ---

@app.post("/v1/maintenance/sync-to-remote")
async def sync_remote():
    """
    Example of a logic-heavy function that uses direct requests 
    instead of an abstracted client, making mocking impossible.
    """
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM blob_store LIMIT 10").fetchall()
    
    results = []
    for row in rows:
        # Manual HTTP post with no retry logic or timeout
        r = requests.post("https://legacy-partner-api.com/ingest", 
                          data={'key': row[0], 'val': row[1]})
        results.append(r.status_code)
    
    return {"synced": len(results), "codes": results}

if __name__ == "__main__":
    import uvicorn
    # Hardcoded port with no environment variable override
    print(f"Server starting on {DB_PATH}")
    uvicorn.run(app, host="127.0.0.1", port=5000)