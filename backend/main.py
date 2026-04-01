from fastapi import FastAPI, UploadFile, File, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import asyncio

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup
    yield
    # Teardown

app = FastAPI(title="LLM Migration Factory API", lifespan=lifespan)

# Allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/upload")
async def upload_script(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Endpoint to receive a python script and start the migration pipeline.
    """
    content = await file.read()
    script_content = content.decode("utf-8")
    
    # In a real app we would generate a unique ID and store it
    job_id = "job-12345"
    
    # background_tasks.add_task(run_pipeline, job_id, script_content)
    
    return {"job_id": job_id, "status": "started"}

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    Stream live pipeline logs to the frontend via WebSocket.
    """
    await websocket.accept()
    # Mock data stream for testing the UI
    try:
        await websocket.send_json({"type": "log", "message": f"➜ Initializing migration job: {job_id}"})
        await asyncio.sleep(1)
        await websocket.send_json({"type": "log", "message": "➜ Parsing syntax tree..."})
        await asyncio.sleep(1)
        await websocket.send_json({"type": "step", "step": "parsing", "status": "complete"})
        # Will replace with actual DB subscription later
    except Exception as e:
        pass
    finally:
        await websocket.close()
