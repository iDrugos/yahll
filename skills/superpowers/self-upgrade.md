---
name: yahll-self-upgrade
description: Use when Yahll is asked to improve itself (/upgrade command) — the exact protocol for safe self-modification with snapshots and tests.
---

# Yahll Self-Upgrade Protocol

## The Rule

Yahll can modify its own code — but safely:
1. Snapshot first
2. Tests must pass before AND after
3. Commit every change

## /upgrade Command Flow

```
User: /upgrade
    │
    ▼
1. Run: self_list() → see all source files
    │
    ▼
2. Identify improvement opportunity
   (new tool? better error handling? faster loop?)
    │
    ▼
3. Run: pytest tests/ → must be ALL GREEN before touching anything
    │
    ▼
4. Run: self_read("file/to/change.py") → read current code
    │
    ▼
5. Snapshot auto-created when self_write is called
    │
    ▼
6. Run: self_write("file/to/change.py", new_content)
    │
    ▼
7. Run: bash_execute("pytest tests/ -v") → must still be ALL GREEN
    │
    ▼
8. Report what changed and why
    │
    ▼
9. Save patch with self_improvements field populated
```

## Safe Self-Modification Rules

- **Never modify `self_tools.py` or `patches.py`** without extra caution — these are the safety systems
- **Always read before writing** — use `self_read` to get current content first
- **One file at a time** — don't modify multiple files in same upgrade
- **Snapshot is automatic** — `self_write` calls `_snapshot_version()` before writing
- **Rollback path**: `patches/snapshot-TIMESTAMP/src/` has the old version

## Rollback Procedure

If tests fail after self_write:

```bash
# List snapshots
ls "C:/Users/Drugos-Laptop/Desktop/Yahll Project/patches/"

# Find latest snapshot, e.g. snapshot-20260404-143022
# Copy old file back:
cp "patches/snapshot-20260404-143022/src/yahll/tools/bash.py" "src/yahll/tools/bash.py"

# Verify tests pass again
pytest tests/ -v
```

## What Makes a Good Self-Improvement

Good:
- Adding a new tool (web_search, clipboard, screenshot)
- Better error messages
- Smarter session summarization
- Faster streaming display

Bad:
- Changing core agent loop without understanding it
- Removing existing tests
- Hardcoding paths or credentials
- Adding features the user didn't ask for (YAGNI)

## Tracking Self-Improvements

In the session patch, populate `self_improvements`:
```json
{
  "self_improvements": [
    "Added web_search tool using DuckDuckGo API",
    "Improved session summary — now asks model instead of using first message"
  ]
}
```

This makes it visible in `/history` and `PATCH-NOTES.md`.
