import threading
import asyncio
from typing import Dict, Optional, List
from models import JobStatus, JobPhase, LogEntry


class JobStore:
    """Thread-safe in-memory store for migration jobs."""

    def __init__(self):
        self._jobs: Dict[str, JobStatus] = {}
        self._lock = threading.Lock()
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}

    def create_job(self, job_id: str, filename: str) -> JobStatus:
        job = JobStatus(job_id=job_id, filename=filename)
        with self._lock:
            self._jobs[job_id] = job
            self._subscribers[job_id] = []
        return job

    def get_job(self, job_id: str) -> Optional[JobStatus]:
        with self._lock:
            return self._jobs.get(job_id)

    def set_phase(self, job_id: str, phase: JobPhase):
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.phase = phase
        self._notify(job_id, {"type": "phase", "phase": phase.value})

    def add_log(self, job_id: str, message: str, level: str = "info"):
        entry = LogEntry(level=level, message=message)
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.logs.append(entry)
        self._notify(job_id, {"type": "log", "level": level, "message": message})

    def set_report(self, job_id: str, report):
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.report = report
        self._notify(job_id, {"type": "report_ready"})

    def set_error(self, job_id: str, error: str):
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.phase = JobPhase.FAILED
                job.error = error
        self._notify(job_id, {"type": "error", "message": error})

    def subscribe(self, job_id: str, queue: asyncio.Queue):
        with self._lock:
            if job_id in self._subscribers:
                self._subscribers[job_id].append(queue)

    def unsubscribe(self, job_id: str, queue: asyncio.Queue):
        with self._lock:
            if job_id in self._subscribers:
                try:
                    self._subscribers[job_id].remove(queue)
                except ValueError:
                    pass

    def _notify(self, job_id: str, event: dict):
        with self._lock:
            queues = list(self._subscribers.get(job_id, []))
        for q in queues:
            try:
                q.put_nowait(event)
            except Exception:
                pass


# Singleton
job_store = JobStore()
