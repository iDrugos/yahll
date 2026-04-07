import os
import subprocess
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


# --- upgrades.py tests ---

def test_run_tests_returns_true_on_success():
    with mock_patch("yahll.memory.upgrades.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="30 passed", stderr="")
        from yahll.memory.upgrades import run_tests
        passed, output = run_tests()
    assert passed is True
    assert "30 passed" in output


def test_run_tests_returns_false_on_failure():
    with mock_patch("yahll.memory.upgrades.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="2 failed", stderr="")
        from yahll.memory.upgrades import run_tests
        passed, output = run_tests()
    assert passed is False
    assert "2 failed" in output


def test_bump_patch_version_increments_correctly():
    import yahll.memory.upgrades as upg_module
    with tempfile.TemporaryDirectory() as d:
        pyproject = os.path.join(d, "pyproject.toml")
        with open(pyproject, "w") as f:
            f.write('[project]\nversion = "0.1.1"\n')
        with mock_patch.object(upg_module, "PYPROJECT_PATH", pyproject):
            from yahll.memory.upgrades import bump_patch_version
            new_ver = bump_patch_version()
        assert new_ver == "0.1.2"
        with open(pyproject) as f:
            assert "0.1.2" in f.read()


def test_bump_patch_version_from_zero():
    import yahll.memory.upgrades as upg_module
    with tempfile.TemporaryDirectory() as d:
        pyproject = os.path.join(d, "pyproject.toml")
        with open(pyproject, "w") as f:
            f.write('[project]\nversion = "0.1.0"\n')
        with mock_patch.object(upg_module, "PYPROJECT_PATH", pyproject):
            from yahll.memory.upgrades import bump_patch_version
            new_ver = bump_patch_version()
        assert new_ver == "0.1.1"


def test_git_commit_upgrade_returns_true_on_success():
    with mock_patch("yahll.memory.upgrades.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        from yahll.memory.upgrades import git_commit_upgrade
        ok, msg = git_commit_upgrade("add retry logic", "0.1.2")
    assert ok is True
    assert "0.1.2" in msg
    assert "add retry logic" in msg


def test_git_commit_upgrade_returns_false_on_failure():
    with mock_patch("yahll.memory.upgrades.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        from yahll.memory.upgrades import git_commit_upgrade
        ok, msg = git_commit_upgrade("some plan", "0.1.2")
    assert ok is False
