from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from contextlib import asynccontextmanager
import asyncio
import uuid
import threading

from models import JobPhase
from job_store import job_store
from parser.ast_parser import parse_openai_calls
from pipeline.orchestrator import run_pipeline
from config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="LLM Migration Factory API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/config")
def public_config():
    """Non-secret configuration for the UI (must match backend .env)."""
    return {
        "source_model": config.SOURCE_MODEL,
        "source_base_url": config.SOURCE_BASE_URL,
        "source_label": config.SOURCE_LABEL,
        "target_provider": config.TARGET_PROVIDER,
        "target_model": config.TARGET_MODEL,
        "target_base_url": config.TARGET_BASE_URL,
        "target_label": config.TARGET_LABEL,
        "target_api_key_env_var": config.TARGET_API_KEY_ENV_VAR,
        "judge_model": config.JUDGE_MODEL,
        "judge_base_url": config.JUDGE_BASE_URL,
        "judge_label": config.JUDGE_LABEL,
        "optimizer_model": config.OPTIMIZER_MODEL,
        "optimizer_base_url": config.OPTIMIZER_BASE_URL,
        "optimizer_label": config.OPTIMIZER_LABEL,
        "optimization_threshold": config.OPTIMIZATION_THRESHOLD,
        "optimization_max_iterations": config.OPTIMIZATION_MAX_ITERATIONS,
        "use_mock_apis": config.USE_MOCK_APIS,
    }


@app.post("/api/upload")
async def upload_script(file: UploadFile = File(...)):
    """
    Accept a Python script and kick off the full migration pipeline
    in a background thread. Returns job_id immediately.
    """
    content = await file.read()
    script_content = content.decode("utf-8")
    filename = file.filename or "unknown.py"

    # Generate unique job ID
    job_id = f"job-{uuid.uuid4().hex[:8]}"

    # Create job in store
    job_store.create_job(job_id, filename)
    job_store.add_log(job_id, f"Received file: {filename}")

    # Quick parse to validate the file has OpenAI calls before starting pipeline
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

    # Launch the full pipeline in a background thread
    thread = threading.Thread(
        target=run_pipeline,
        args=(job_id, script_content, filename),
        daemon=True,
    )
    thread.start()

    return {
        "job_id": job_id,
        "filename": filename,
        "call_sites_found": len(raw_calls),
        "status": "pipeline_started",
    }


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    """Poll the current status and logs of a job."""
    job = job_store.get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    return job.model_dump()


@app.get("/api/jobs/{job_id}/report")
def get_job_report(job_id: str):
    """Get the final migration report for a completed job."""
    job = job_store.get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    if not job.report:
        return JSONResponse(status_code=202, content={"message": "Report not ready yet", "phase": job.phase.value})
    return job.report.model_dump()


@app.get("/api/jobs/{job_id}/download")
def download_refactored(job_id: str):
    """Download the refactored Python source file."""
    job = job_store.get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    if not job.report or not job.report.refactored_code:
        return JSONResponse(status_code=202, content={"message": "Refactored code not ready yet"})

    return PlainTextResponse(
        content=job.report.refactored_code,
        media_type="text/x-python",
        headers={"Content-Disposition": f'attachment; filename="refactored_{job.filename}"'},
    )


@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """Stream live pipeline events to the frontend via WebSocket."""
    await websocket.accept()

    loop = asyncio.get_event_loop()
    queue: asyncio.Queue = asyncio.Queue()
    job_store.subscribe(job_id, queue, loop)

    try:
        # Send existing logs first
        job = job_store.get_job(job_id)
        if job:
            for log in job.logs:
                await websocket.send_json({"type": "log", "level": log.level, "message": log.message})
            await websocket.send_json({"type": "phase", "phase": job.phase.value})

            # If the job already completed before we connected, send report_ready and exit
            if job.phase in (JobPhase.COMPLETE, JobPhase.FAILED):
                if job.report:
                    await websocket.send_json({"type": "report_ready"})
                return

        # Stream new events
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=120.0)
                await websocket.send_json(event)

                # Stop streaming when job is done
                if event.get("type") == "phase" and event.get("phase") in ("complete", "failed"):
                    break
                if event.get("type") == "error":
                    break
                if event.get("type") == "report_ready":
                    break
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        job_store.unsubscribe(job_id, queue)

