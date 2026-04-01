import json
import os
import threading
import asyncio
from typing import Dict, Optional, List
from models import JobStatus, JobPhase, LogEntry


class JobStore:
    """Thread-safe in-memory store for migration jobs.

    Uses threading and a simple list-based pub/sub
    that is safe to call from both sync threads and the async event loop.
    Subclass and override _persist_job / _load_from_remote for remote backing stores.
    """

    def __init__(self):
        self._jobs: Dict[str, JobStatus] = {}
        self._lock = threading.Lock()
        self._subscribers: Dict[str, List[tuple]] = {}

    def _persist_job(self, job_id: str) -> None:
        """Called after mutations; override to persist (e.g. DynamoDB)."""
        return

    def _load_from_remote(self, job_id: str) -> Optional[JobStatus]:
        """Override to hydrate from remote storage when not in memory."""
        return None

    def create_job(self, job_id: str, filename: str) -> JobStatus:
        job = JobStatus(job_id=job_id, filename=filename)
        with self._lock:
            self._jobs[job_id] = job
            self._subscribers[job_id] = []
        self._persist_job(job_id)
        return job

    def get_job(self, job_id: str) -> Optional[JobStatus]:
        with self._lock:
            local = self._jobs.get(job_id)
        if local is not None:
            return local
        remote = self._load_from_remote(job_id)
        return remote

    def set_phase(self, job_id: str, phase: JobPhase):
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.phase = phase
        self._persist_job(job_id)
        self._notify(job_id, {"type": "phase", "phase": phase.value})

    def add_log(self, job_id: str, message: str, level: str = "info"):
        entry = LogEntry(level=level, message=message)
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.logs.append(entry)
        self._persist_job(job_id)
        self._notify(job_id, {"type": "log", "level": level, "message": message})

    def set_report(self, job_id: str, report):
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.report = report
        self._persist_job(job_id)
        self._notify(job_id, {"type": "report_ready"})

    def set_error(self, job_id: str, error: str):
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.phase = JobPhase.FAILED
                job.error = error
        self._persist_job(job_id)
        self._notify(job_id, {"type": "error", "message": error})

    def subscribe(self, job_id: str, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        with self._lock:
            if job_id in self._subscribers:
                self._subscribers[job_id].append((loop, queue))

    def unsubscribe(self, job_id: str, queue: asyncio.Queue):
        with self._lock:
            if job_id in self._subscribers:
                self._subscribers[job_id] = [
                    (l, q) for l, q in self._subscribers[job_id] if q is not queue
                ]

    def _notify(self, job_id: str, event: dict):
        with self._lock:
            subs = list(self._subscribers.get(job_id, []))
        for loop, q in subs:
            try:
                loop.call_soon_threadsafe(q.put_nowait, event)
            except Exception:
                pass


class DynamoDBJobStore(JobStore):
    """Persists job rows to DynamoDB (partition key: job_id)."""

    def __init__(self, table_name: str, region: str | None = None):
        super().__init__()
        import boto3

        self._table_name = table_name
        self._ddb = boto3.resource("dynamodb", region_name=region or os.environ.get("AWS_REGION", "us-east-1"))
        self._table = self._ddb.Table(table_name)

    def _persist_job(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
        if not job:
            return
        self._table.put_item(Item={"job_id": job_id, "payload": job.model_dump_json()})

    def _load_from_remote(self, job_id: str) -> Optional[JobStatus]:
        try:
            r = self._table.get_item(Key={"job_id": job_id})
        except Exception:
            return None
        item = r.get("Item")
        if not item or "payload" not in item:
            return None
        raw = item["payload"]
        if isinstance(raw, dict):
            payload = json.dumps(raw)
        else:
            payload = str(raw)
        job = JobStatus.model_validate_json(payload)
        with self._lock:
            self._jobs[job_id] = job
            if job_id not in self._subscribers:
                self._subscribers[job_id] = []
        return job


def _make_job_store() -> JobStore:
    backend = os.environ.get("JOB_STORE_BACKEND", "memory").lower().strip()
    if backend == "dynamodb":
        table = os.environ.get("JOBS_TABLE_NAME", "").strip()
        if not table:
            raise RuntimeError("JOBS_TABLE_NAME is required when JOB_STORE_BACKEND=dynamodb")
        return DynamoDBJobStore(table)
    return JobStore()


job_store: JobStore = _make_job_store()
