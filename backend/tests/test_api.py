"""API smoke tests (no external LLM calls)."""
import os

os.environ.setdefault("JOB_STORE_BACKEND", "memory")

from fastapi.testclient import TestClient

from main import app


def test_health():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_public_config():
    c = TestClient(app)
    r = c.get("/api/config")
    assert r.status_code == 200
    data = r.json()
    assert "source_model" in data
    assert "target_model" in data
    assert "judge_model" in data
    assert "optimizer_model" in data
    assert "optimization_threshold" in data
    assert "use_mock_apis" in data
    # Raw secret fields must never appear (env var names are ok)
    assert "source_api_key" not in data
    assert "target_api_key" not in data
    assert "judge_api_key" not in data
    assert "optimizer_api_key" not in data
