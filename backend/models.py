from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class JobPhase(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    GOLDEN_CAPTURE = "golden_capture"
    OPTIMIZING = "optimizing"
    REFACTORING = "refactoring"
    COMPLETE = "complete"
    FAILED = "failed"


class LogEntry(BaseModel):
    level: str = "info"   # info | warn | error | success
    message: str
    phase: Optional[JobPhase] = None


class CallSite(BaseModel):
    lineno: int
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    raw_snippet: str

    @property
    def system_prompt(self) -> Optional[str]:
        for m in self.messages:
            if m.get("role") == "system":
                return m.get("content")
        return None

    @property
    def user_prompt(self) -> Optional[str]:
        for m in self.messages:
            if m.get("role") == "user":
                return m.get("content")
        return None


class GoldenResponse(BaseModel):
    call_site_lineno: int
    original_messages: List[Dict[str, Any]]
    response_text: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float


class OptimizationIteration(BaseModel):
    iteration: int
    translated_system_prompt: str
    translated_user_prompt: str
    target_response: str
    score: float
    judge_feedback: str
    passed: bool


class OptimizationResult(BaseModel):
    call_site_lineno: int
    iterations: List[OptimizationIteration] = Field(default_factory=list)
    final_system_prompt: str
    final_user_prompt: str
    final_score: float
    target_response: str
    target_latency_ms: float


class MigrationReport(BaseModel):
    job_id: str
    filename: str
    total_call_sites: int
    golden_responses: List[GoldenResponse] = Field(default_factory=list)
    optimization_results: List[OptimizationResult] = Field(default_factory=list)
    avg_semantic_score: float = 0.0
    original_cost_usd: float = 0.0
    target_cost_usd: float = 0.0
    cost_savings_pct: float = 0.0
    avg_original_latency_ms: float = 0.0
    avg_target_latency_ms: float = 0.0
    refactored_code: Optional[str] = None


class JobStatus(BaseModel):
    job_id: str
    filename: str
    phase: JobPhase = JobPhase.PENDING
    logs: List[LogEntry] = Field(default_factory=list)
    report: Optional[MigrationReport] = None
    error: Optional[str] = None
