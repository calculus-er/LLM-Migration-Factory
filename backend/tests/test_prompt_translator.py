"""Tests for prompt translator parsing."""
import os

os.environ.setdefault("JOB_STORE_BACKEND", "memory")

from optimizer.prompt_translator import _parse_translation


def test_parse_multiline_user_prompt():
    raw = """SYSTEM_PROMPT: You summarize text.

USER_PROMPT: Please read and bullet the core points.

Paragraph one here.
Paragraph two here.
"""
    out = _parse_translation(raw)
    assert "Paragraph one" in out["user_prompt"]
    assert "Paragraph two" in out["user_prompt"]
    assert "You summarize" in out["system_prompt"]


def test_parse_single_line_fallback():
    raw = "SYSTEM_PROMPT: A\nUSER_PROMPT: B"
    out = _parse_translation(raw)
    assert out["system_prompt"] == "A"
    assert out["user_prompt"] == "B"
