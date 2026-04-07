# Yahll Phase 3 — Self-Upgrade System
**Spec Date:** 2026-04-07  
**Status:** Approved  
**Author:** Drugos + Claude  

---

## Vision

`/upgrade` becomes a safe, autonomous, test-verified self-improvement loop. Yahll audits its own source, picks the best improvement, applies it, runs tests, and commits — or rolls back automatically if tests fail. Zero user confirmation required. Zero model control over the safety net.

---

## Pipeline (5 Steps)

```
/upgrade
    │
    ▼
1. AUDIT     — self_list + self_read 3-4 files → find best improvement target
    │
    ▼
2. PLAN      — model outputs one concrete improvement goal as plain text
    │
    ▼
3. APPLY     — model implements plan via self_write (one file only)
    │
    ▼
4. TEST      — pytest tests/ -v via bash_execute, parse pass/fail count
    │
    ├── PASS → bump patch version in pyproject.toml, git add + git commit
    │
    └── FAIL → restore file from in-memory snapshot, report failed tests
```

---

## Components

### `src/yahll/memory/snapshots.py` (new)
- `snapshot_source() -> dict[str, str]` — reads all `.py` files in `src/yahll/` into a `{path: content}` dict
- `restore_snapshot(snapshot: dict)` — writes all files back from snapshot dict

### `src/yahll/memory/upgrades.py` (new)
- `bump_patch_version() -> str` — reads `pyproject.toml`, increments patch number (0.1.1 → 0.1.2), writes back, returns new version
- `git_commit_upgrade(plan: str, version: str)` — runs `git add src/ pyproject.toml` + `git commit -m "self-upgrade v{version}: {plan}"`
- `run_tests() -> tuple[bool, str]` — runs `pytest tests/ -v`, returns (passed: bool, output: str)

### `/upgrade` in `main.py` (modified)
Replaces the current one-liner with the full 5-step pipeline. The model handles steps 1-3 via `agent.chat()`. Steps 4-5 are deterministic Python — the model cannot skip or alter them.

---

## Upgrade Prompt (sent to model in step 1)

```
You are upgrading yourself. Follow these steps exactly:

1. Use self_list to see all your source files.
2. Use self_read to read 3-4 files — pick ones most likely to have room for improvement.
3. Choose ONE file to improve. Look for: missing error handling, repeated code, 
   slow patterns, hardcoded values that should be configurable, missing edge cases.
4. State your improvement plan in ONE sentence starting with "PLAN:"
5. Implement the improvement using self_write. Change ONE file only.
6. Confirm what you changed.

Do not change tests. Do not change pyproject.toml. Do not change main.py.
```

---

## Error Handling

| Situation | Behaviour |
|-----------|-----------|
| Tests fail after apply | Restore from snapshot, report which tests failed, no commit |
| Model writes outside `src/yahll/` | Blocked by `self_write` path scoping |
| Model makes no changes | Detect no diff between snapshot and current files, skip test+commit, report "nothing changed" |
| `pytest` crashes / not found | Treat as failure, rollback |
| Git not configured / dirty tree | Skip git commit, still bump version, warn user |
| Ollama times out during audit | Abort before any files touched, report timeout |

---

## Output to User

```
[cyan]Yahll is upgrading itself...[/cyan]

Auditing source files...
Plan: add retry logic to ollama_client.py when connection drops

Applying improvement...
Running tests...

✓ 30/30 tests passed
✓ Version bumped: 0.1.1 → 0.1.2
✓ Committed: self-upgrade v0.1.2: add retry logic to ollama_client.py
```

On failure:
```
✗ 3 tests failed — rolling back
  Restored: src/yahll/core/ollama_client.py
  No version bump. No commit.
```

---

## Files Changed

| File | Change |
|------|--------|
| `src/yahll/memory/snapshots.py` | New — snapshot + restore |
| `src/yahll/memory/upgrades.py` | New — version bump + git commit + test runner |
| `src/yahll/main.py` | Modify `/upgrade` handler — 5-step pipeline |
| `tests/test_upgrades.py` | New — tests for snapshot, restore, version bump |

---

## Success Criteria

- [ ] `/upgrade` runs the full 5-step pipeline without user input
- [ ] Tests are always run — model cannot skip them
- [ ] Rollback restores exact original file content on test failure
- [ ] Patch version auto-increments on success
- [ ] Git commit created on success with descriptive message
- [ ] All new code covered by tests
