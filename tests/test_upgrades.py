import os
import tempfile
import pytest
from unittest.mock import patch as mock_patch, MagicMock
from yahll.memory import snapshots as snap_module
from yahll.memory.snapshots import snapshot_source, restore_snapshot


def test_snapshot_captures_all_py_files():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "core"))
        with open(os.path.join(d, "main.py"), "w") as f:
            f.write("# main")
        with open(os.path.join(d, "core", "agent.py"), "w") as f:
            f.write("# agent")

        with mock_patch.object(snap_module, "YAHLL_SRC", d):
            snap = snapshot_source()

        assert any("main.py" in p for p in snap)
        assert any("agent.py" in p for p in snap)
        assert all(isinstance(v, str) for v in snap.values())


def test_restore_snapshot_rewrites_files():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "tool.py")
        with open(path, "w") as f:
            f.write("original content")

        with mock_patch.object(snap_module, "YAHLL_SRC", d):
            snap = snapshot_source()

        with open(path, "w") as f:
            f.write("corrupted content")

        # restore_snapshot uses absolute paths from snap dict — no YAHLL_SRC needed
        failed = restore_snapshot(snap)
        assert failed == []
        with open(path) as f:
            assert f.read() == "original content"


def test_snapshot_detects_changed_files():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "tool.py")
        with open(path, "w") as f:
            f.write("before")

        with mock_patch.object(snap_module, "YAHLL_SRC", d):
            before = snapshot_source()

        with open(path, "w") as f:
            f.write("after")

        with mock_patch.object(snap_module, "YAHLL_SRC", d):
            after = snapshot_source()

        changed = [p for p, c in after.items() if before.get(p) != c]
        assert len(changed) == 1
        assert "tool.py" in changed[0]


def test_restore_snapshot_returns_empty_on_success():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "file.py")
        with open(path, "w") as f:
            f.write("content")
        snap = {path: "content"}
        failed = restore_snapshot(snap)
        assert failed == []


def test_restore_snapshot_returns_failed_paths():
    # Simulate a path that can't be written (directory instead of file)
    with tempfile.TemporaryDirectory() as d:
        bad_path = os.path.join(d, "nonexistent_dir", "file.py")
        snap = {bad_path: "content"}
        failed = restore_snapshot(snap)
        assert bad_path in failed
