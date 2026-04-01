from fastapi import FastAPI, UploadFile, File, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import asyncio
import uuid

from models import JobPhase, CallSite
from job_store import job_store
from parser.ast_parser import parse_openai_calls

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="LLM Migration Factory API", lifespan=lifespan)

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
async def upload_script(file: UploadFile = File(...)):
    """
    Accept a Python script, parse it for OpenAI calls, create a job,
    and return the job ID + parsed call sites.
    """
    content = await file.read()
    script_content = content.decode("utf-8")

    # Generate unique job ID
    job_id = f"job-{uuid.uuid4().hex[:8]}"

    # Create job in store
    job = job_store.create_job(job_id, file.filename or "unknown.py")

    # Phase 1: Parse the file
    job_store.set_phase(job_id, JobPhase.PARSING)
    job_store.add_log(job_id, f"Received file: {file.filename}")

    try:
        raw_calls = parse_openai_calls(script_content)
    except SyntaxError as e:
        job_store.set_error(job_id, f"Python syntax error: {e}")
        return JSONResponse(status_code=400, content={"error": str(e), "job_id": job_id})

    if not raw_calls:
        job_store.add_log(job_id, "No OpenAI call sites found in the file.", level="warn")
        return JSONResponse(
            status_code=200,
            content={"job_id": job_id, "call_sites": [], "message": "No OpenAI calls detected."},
        )

    # Convert to Pydantic models
    call_sites = []
    for c in raw_calls:
        site = CallSite(
            lineno=c.lineno,
            model=c.args.get("model"),
            temperature=c.args.get("temperature"),
            max_tokens=c.args.get("max_tokens"),
            messages=c.args.get("messages", []),
            raw_snippet=c.raw_snippet,
        )
        call_sites.append(site)
        job_store.add_log(job_id, f"Found call site at line {c.lineno}: model={c.args.get('model')}")

    job_store.add_log(job_id, f"Parsing complete. {len(call_sites)} call site(s) found.", level="success")

    # Store script content on the job for later phases
    # (We attach it as extra data since JobStatus doesn't have a field for it)
    job._script_content = script_content
    job._call_sites = call_sites

    return {
        "job_id": job_id,
        "filename": file.filename,
        "call_sites": [s.model_dump() for s in call_sites],
        "status": "parsed",
    }


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    """Poll the current status and logs of a job."""
    job = job_store.get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    return job.model_dump()


@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """Stream live pipeline events to the frontend via WebSocket."""
    await websocket.accept()

    queue: asyncio.Queue = asyncio.Queue()
    job_store.subscribe(job_id, queue)

    try:
        # Send existing logs first
        job = job_store.get_job(job_id)
        if job:
            for log in job.logs:
                await websocket.send_json({"type": "log", "level": log.level, "message": log.message})
            await websocket.send_json({"type": "phase", "phase": job.phase.value})

        # Stream new events
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=60.0)
                await websocket.send_json(event)

                # Stop streaming when job is done
                if event.get("type") == "phase" and event.get("phase") in ("complete", "failed"):
                    break
                if event.get("type") == "error":
                    break
                if event.get("type") == "report_ready":
                    break
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        pass
    finally:
        job_store.unsubscribe(job_id, queue)
