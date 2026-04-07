# Phase 3 Self-Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give Yahll a safe, autonomous self-improvement loop — `/upgrade` audits source, applies one improvement, runs tests, commits on success, rolls back on failure.

**Architecture:** Model handles audit+plan+apply (steps 1-3) via `agent.chat()`. Deterministic Python handles test+commit/rollback (steps 4-5) — the model cannot skip the safety net. In-memory snapshot taken before the model runs; restored if tests fail.

**Tech Stack:** Python, pytest, subprocess (git, pytest), Rich console, re (plan extraction)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/yahll/memory/snapshots.py` | Create | In-memory snapshot + restore of all `src/yahll/` `.py` files |
| `src/yahll/memory/upgrades.py` | Create | `run_tests()`, `bump_patch_version()`, `git_commit_upgrade()` |
| `tests/test_upgrades.py` | Create | Tests for snapshots + upgrades |
| `src/yahll/main.py` | Modify | Replace `/upgrade` handler with 5-step pipeline |

---

## Task 1: `snapshots.py` — in-memory snapshot and restore

**Files:**
- Create: `src/yahll/memory/snapshots.py`
- Test: `tests/test_upgrades.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_upgrades.py`:

```python
import os
import tempfile
import pytest
from unittest.mock import patch as mock_patch


def test_snapshot_captures_all_py_files():
    with tempfile.TemporaryDirectory() as d:
        # Create fake source files
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

        # Corrupt the file
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
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_upgrades.py -v
```
Expected: `ImportError` — `snapshots` module does not exist yet.

- [ ] **Step 3: Create `src/yahll/memory/snapshots.py`**

```python
import os
import glob

# Same resolution as self_tools.py — points to src/yahll/
YAHLL_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def snapshot_source() -> dict:
    """Read all .py files in src/yahll/ into {absolute_path: content} dict."""
    snapshot = {}
    for path in glob.glob(os.path.join(YAHLL_SRC, "**", "*.py"), recursive=True):
        try:
            with open(path, "r", encoding="utf-8") as f:
                snapshot[path] = f.read()
        except Exception:
            pass
    return snapshot


def restore_snapshot(snapshot: dict):
    """Write all files back from snapshot dict."""
    for path, content in snapshot.items():
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass
```

- [ ] **Step 4: Run tests — expect pass**

```
pytest tests/test_upgrades.py -v
```
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add src/yahll/memory/snapshots.py tests/test_upgrades.py
git commit -m "feat: add in-memory source snapshot and restore"
```

---

## Task 2: `upgrades.py` — test runner, version bumper, git commit

**Files:**
- Create: `src/yahll/memory/upgrades.py`
- Modify: `tests/test_upgrades.py` (append new tests)

- [ ] **Step 1: Append failing tests to `tests/test_upgrades.py`**

```python
from unittest.mock import MagicMock, patch as mock_patch


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
    with tempfile.TemporaryDirectory() as d:
        pyproject = os.path.join(d, "pyproject.toml")
        open(pyproject, "w").write('[project]\nversion = "0.1.1"\n')

        with mock_patch("yahll.memory.upgrades.PYPROJECT_PATH", pyproject):
            from yahll.memory.upgrades import bump_patch_version
            new_ver = bump_patch_version()

        assert new_ver == "0.1.2"
        assert '0.1.2' in open(pyproject).read()


def test_bump_patch_version_from_zero():
    with tempfile.TemporaryDirectory() as d:
        pyproject = os.path.join(d, "pyproject.toml")
        open(pyproject, "w").write('[project]\nversion = "0.1.0"\n')

        with mock_patch("yahll.memory.upgrades.PYPROJECT_PATH", pyproject):
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
    import subprocess
    with mock_patch("yahll.memory.upgrades.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        from yahll.memory.upgrades import git_commit_upgrade
        ok, msg = git_commit_upgrade("some plan", "0.1.2")
    assert ok is False
```

- [ ] **Step 2: Run tests — expect fail**

```
pytest tests/test_upgrades.py -v
```
Expected: `ImportError` — `upgrades` module does not exist yet.

- [ ] **Step 3: Create `src/yahll/memory/upgrades.py`**

```python
import os
import re
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))  # src/yahll/memory/
PROJECT_ROOT = os.path.normpath(os.path.join(_HERE, "..", "..", ".."))  # Yahll Project/
PYPROJECT_PATH = os.path.join(PROJECT_ROOT, "pyproject.toml")


def run_tests() -> tuple[bool, str]:
    """Run pytest, return (passed, combined output)."""
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "-v"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    output = result.stdout + result.stderr
    return result.returncode == 0, output


def bump_patch_version() -> str:
    """Increment patch version in pyproject.toml. Returns new version string."""
    with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
    if not match:
        return "0.0.0"

    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    new_version = f"{major}.{minor}.{patch + 1}"
    new_content = content.replace(match.group(0), f'version = "{new_version}"')

    with open(PYPROJECT_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    return new_version


def git_commit_upgrade(plan: str, version: str) -> tuple[bool, str]:
    """Stage src/ and pyproject.toml, commit. Returns (success, commit message)."""
    msg = f"self-upgrade v{version}: {plan}"
    try:
        subprocess.run(
            ["git", "add", "src/", "pyproject.toml"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
        )
        return True, msg
    except subprocess.CalledProcessError as e:
        return False, str(e)
```

- [ ] **Step 4: Run tests — expect pass**

```
pytest tests/test_upgrades.py -v
```
Expected: `9 passed`

- [ ] **Step 5: Commit**

```bash
git add src/yahll/memory/upgrades.py tests/test_upgrades.py
git commit -m "feat: add test runner, version bumper, and git commit helper"
```

---

## Task 3: Wire up `/upgrade` in `main.py`

**Files:**
- Modify: `src/yahll/main.py`

- [ ] **Step 1: Add `import re` at the top of `main.py`**

In `src/yahll/main.py`, add `import re` to the existing imports block (after `import json`):

```python
import re
```

- [ ] **Step 2: Add imports for new modules**

Add to the memory imports block in `main.py`:

```python
from yahll.memory.snapshots import snapshot_source, restore_snapshot
from yahll.memory.upgrades import run_tests, bump_patch_version, git_commit_upgrade
```

- [ ] **Step 3: Replace the `/upgrade` handler**

Find and replace the existing `/upgrade` block in `_handle_slash_command`:

Old:
```python
    if command == "/upgrade":
        console.print("[cyan]Yahll is looking at itself...[/cyan]\n")
        response = agent.chat(
            "Use self_list to see your own source files. Then read one file that could be improved, "
            "propose a concrete improvement, implement it with self_write, and confirm what changed."
        )
        console.print(Markdown(response))
        return True
```

New:
```python
    if command == "/upgrade":
        console.print("[cyan]Yahll is upgrading itself...[/cyan]\n")

        from yahll.memory.snapshots import snapshot_source, restore_snapshot
        from yahll.memory.upgrades import run_tests, bump_patch_version, git_commit_upgrade

        # Step 1: Snapshot BEFORE any model changes
        snapshot = snapshot_source()

        # Steps 2-4: Model audits, plans, applies (one file only)
        console.print("[dim]Auditing source files...[/dim]")
        upgrade_prompt = (
            "You are upgrading yourself. Follow these steps exactly:\n\n"
            "1. Use self_list to see all your source files.\n"
            "2. Use self_read to read 3-4 files — pick ones most likely to have room for improvement.\n"
            "3. Choose ONE file to improve. Look for: missing error handling, repeated code,\n"
            "   slow patterns, hardcoded values, missing edge cases.\n"
            "4. State your improvement plan in ONE sentence starting with 'PLAN:'\n"
            "5. Implement the improvement using self_write. Change ONE file only.\n"
            "6. Confirm what you changed.\n\n"
            "Do not change tests. Do not change pyproject.toml. Do not change main.py."
        )
        with console.status("[dim]thinking...[/dim]", spinner="dots"):
            response = agent.chat(upgrade_prompt)

        # Extract plan from model response
        plan_match = re.search(r"PLAN:\s*(.+)", response, re.IGNORECASE)
        plan = plan_match.group(1).strip() if plan_match else "autonomous improvement"
        console.print(f"Plan: [italic]{plan}[/italic]\n")

        # Detect what actually changed
        current = snapshot_source()
        changed = [p for p, c in current.items() if snapshot.get(p) != c]

        if not changed:
            console.print("[yellow]Nothing changed — no improvement applied.[/yellow]")
            return True

        # Step 5: Run tests
        console.print("[dim]Running tests...[/dim]")
        passed, output = run_tests()

        if passed:
            count_match = re.search(r"(\d+) passed", output)
            count = count_match.group(1) if count_match else "all"
            new_version = bump_patch_version()
            ok, commit_msg = git_commit_upgrade(plan, new_version)

            console.print(f"[green]✓ {count} tests passed[/green]")
            console.print(f"[green]✓ Version bumped to {new_version}[/green]")
            if ok:
                console.print(f"[green]✓ Committed: {commit_msg}[/green]")
            else:
                console.print("[yellow]⚠ Git commit failed — version bumped but not committed[/yellow]")
        else:
            restore_snapshot(snapshot)
            fail_match = re.search(r"(\d+) failed", output)
            count = fail_match.group(1) if fail_match else "some"
            console.print(f"[red]✗ {count} tests failed — rolling back[/red]")
            for f in changed:
                rel = os.path.relpath(f)
                console.print(f"[dim]  Restored: {rel}[/dim]")
            console.print("[dim]No version bump. No commit.[/dim]")

        return True
```

- [ ] **Step 4: Run all tests — expect all pass**

```
pytest tests/ -v
```
Expected: `30 passed` (existing tests unchanged)

- [ ] **Step 5: Commit**

```bash
git add src/yahll/main.py
git commit -m "feat: /upgrade now runs full 5-step audit→apply→test→commit pipeline"
```

---

## Task 4: Smoke Test

- [ ] **Step 1: Start Yahll and run `/upgrade`**

```
yahll
> /upgrade
```

Expected output:
```
Yahll is upgrading itself...

Auditing source files...
Plan: <one sentence from model>

Running tests...
✓ 30 tests passed
✓ Version bumped to 0.1.2
✓ Committed: self-upgrade v0.1.2: <plan>
```

- [ ] **Step 2: Verify git log shows the self-upgrade commit**

```bash
git log --oneline -3
```
Expected: top commit message starts with `self-upgrade v0.1.`

- [ ] **Step 3: Verify version bumped in pyproject.toml**

```bash
grep version pyproject.toml
```
Expected: `version = "0.1.2"` (or higher)

- [ ] **Step 4: Update Yahll.md**

Mark Phase 3 complete in `Yahll.md`. Add session entry.
