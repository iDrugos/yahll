import os
import json
import tempfile
import pytest
from unittest.mock import patch as mock_patch
from yahll.memory.patches import save_patch, load_latest_patch, list_patches, build_context_from_patch


def test_save_patch_creates_file():
    with tempfile.TemporaryDirectory() as d:
        with mock_patch("yahll.memory.patches.SESSIONS_DIR", d):
            save_patch({"summary": "test session", "learned": []})
            files = os.listdir(d)
            assert len(files) == 1
            assert files[0].endswith(".json")


def test_save_patch_content_is_correct():
    with tempfile.TemporaryDirectory() as d:
        with mock_patch("yahll.memory.patches.SESSIONS_DIR", d):
            save_patch({"summary": "built the agent", "learned": ["user likes Python"]})
            files = os.listdir(d)
            with open(os.path.join(d, files[0])) as f:
                data = json.load(f)
            assert data["summary"] == "built the agent"
            assert "user likes Python" in data["learned"]


def test_load_latest_patch_returns_none_when_empty():
    with tempfile.TemporaryDirectory() as d:
        with mock_patch("yahll.memory.patches.SESSIONS_DIR", d):
            assert load_latest_patch() is None


def test_load_latest_patch_returns_most_recent():
    with tempfile.TemporaryDirectory() as d:
        with mock_patch("yahll.memory.patches.SESSIONS_DIR", d):
            save_patch({"summary": "first"})
            save_patch({"summary": "second"})
            result = load_latest_patch()
            assert result["summary"] == "second"


def test_build_context_includes_summary_and_learned():
    patch = {
        "timestamp": "2026-04-04T12:00:00",
        "summary": "built Ollama client",
        "learned": ["user prefers Python"],
        "next_context": "start Task 3",
    }
    ctx = build_context_from_patch(patch)
    assert "built Ollama client" in ctx
    assert "user prefers Python" in ctx
    assert "start Task 3" in ctx
