import os
import tempfile
import pytest
from unittest.mock import patch as mock_patch


def test_snapshot_captures_all_py_files():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "core"))
        open(os.path.join(d, "main.py"), "w").write("# main")
        open(os.path.join(d, "core", "agent.py"), "w").write("# agent")

        with mock_patch("yahll.memory.snapshots.YAHLL_SRC", d):
            from yahll.memory.snapshots import snapshot_source
            snap = snapshot_source()

        assert any("main.py" in p for p in snap)
        assert any("agent.py" in p for p in snap)
        assert all(isinstance(v, str) for v in snap.values())


def test_restore_snapshot_rewrites_files():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "tool.py")
        open(path, "w").write("original content")

        with mock_patch("yahll.memory.snapshots.YAHLL_SRC", d):
            from yahll.memory.snapshots import snapshot_source, restore_snapshot
            snap = snapshot_source()

        open(path, "w").write("corrupted content")
        restore_snapshot(snap)
        assert open(path).read() == "original content"


def test_snapshot_detects_changed_files():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "tool.py")
        open(path, "w").write("before")

        with mock_patch("yahll.memory.snapshots.YAHLL_SRC", d):
            from yahll.memory.snapshots import snapshot_source
            before = snapshot_source()

        open(path, "w").write("after")

        with mock_patch("yahll.memory.snapshots.YAHLL_SRC", d):
            after = snapshot_source()

        changed = [p for p, c in after.items() if before.get(p) != c]
        assert len(changed) == 1
        assert "tool.py" in changed[0]
