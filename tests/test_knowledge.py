import os
import tempfile
import pytest
from unittest.mock import patch as mock_patch
from yahll.memory.knowledge import load_knowledge, append_knowledge, get_knowledge_context


def test_load_knowledge_returns_empty_when_no_file():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "knowledge.md")
        with mock_patch("yahll.memory.knowledge.KNOWLEDGE_PATH", path):
            assert load_knowledge() == ""


def test_append_knowledge_creates_file():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "knowledge.md")
        with mock_patch("yahll.memory.knowledge.KNOWLEDGE_PATH", path), \
             mock_patch("yahll.memory.knowledge.YAHLL_HOME", d):
            append_knowledge(["installed numpy", "user prefers dark mode"])
            assert os.path.exists(path)
            content = open(path).read()
            assert "installed numpy" in content
            assert "user prefers dark mode" in content


def test_append_knowledge_multiple_times():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "knowledge.md")
        with mock_patch("yahll.memory.knowledge.KNOWLEDGE_PATH", path), \
             mock_patch("yahll.memory.knowledge.YAHLL_HOME", d):
            append_knowledge(["fact one"])
            append_knowledge(["fact two"])
            content = open(path).read()
            assert "fact one" in content
            assert "fact two" in content


def test_get_knowledge_context_returns_empty_when_no_file():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "knowledge.md")
        with mock_patch("yahll.memory.knowledge.KNOWLEDGE_PATH", path):
            assert get_knowledge_context() == ""


def test_get_knowledge_context_returns_recent_facts():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "knowledge.md")
        with mock_patch("yahll.memory.knowledge.KNOWLEDGE_PATH", path), \
             mock_patch("yahll.memory.knowledge.YAHLL_HOME", d):
            append_knowledge(["user is Drugos", "project is Yahll"])
            ctx = get_knowledge_context()
            assert "user is Drugos" in ctx
            assert "project is Yahll" in ctx


def test_append_knowledge_skips_empty_facts():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "knowledge.md")
        with mock_patch("yahll.memory.knowledge.KNOWLEDGE_PATH", path), \
             mock_patch("yahll.memory.knowledge.YAHLL_HOME", d):
            append_knowledge(["", "  ", "valid fact"])
            content = open(path).read()
            assert "valid fact" in content
            # Empty facts should not appear as bare bullet lines
            lines = [l for l in content.splitlines() if l.strip() == "-"]
            assert len(lines) == 0
