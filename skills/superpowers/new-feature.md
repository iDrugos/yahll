---
name: yahll-new-feature
description: Use when adding ANY new feature to Yahll — covers the exact sequence from idea to committed code.
---

# Adding a New Feature to Yahll

## Sequence

```
1. Update Yahll.md — add task to "What's Next"
2. Write failing test
3. Implement
4. Tests pass
5. Update Yahll.md — check off task
6. Update PATCH-NOTES.md
7. Commit
```

## Feature Checklist

- [ ] Does it belong in `tools/`, `core/`, or `memory/`?
- [ ] Is there a test for the happy path?
- [ ] Is there a test for the error case?
- [ ] If it's a tool — is it registered in `registry.py`?
- [ ] If it's a slash command — is it in `_handle_slash_command` in `main.py`?
- [ ] Does `CLAUDE.md` need updating?
- [ ] Does `yahll-architecture.md` need updating?

## New Tool Checklist

1. Create `src/yahll/tools/your_tool.py`
2. Function signature: `def your_tool(param: str) -> dict`
3. Return dict always (never raise exceptions to caller)
4. Add JSON schema to `TOOL_SCHEMAS` in `registry.py`
5. Add to `TOOL_DISPATCH` in `registry.py`
6. Add import in `registry.py`
7. Write test in `tests/test_tools.py`
8. Run `pytest tests/test_tools.py -v` — all pass
9. Commit: `feat: add your_tool tool`

## New Slash Command Checklist

In `main.py → _handle_slash_command`:
```python
if command == "/yourcommand":
    # implement
    return True
```

Update `/help` display string to include the new command.
Write a manual test: run `yahll`, type `/yourcommand`, verify it works.
Commit: `feat: add /yourcommand slash command`

## Planned Future Features (Phase 2+)

| Feature | Where | Notes |
|---------|-------|-------|
| `web_search` tool | `tools/web_search.py` | DuckDuckGo free API, no key needed |
| Smart session summary | `memory/patches.py` | Ask model to summarize instead of truncating |
| `clipboard` tool | `tools/clipboard.py` | Read/write system clipboard |
| `/upgrade` with model suggestion | `main.py` | Yahll proposes specific improvement |
| Token counter display | `main.py` | Show Ollama token usage per response |
| VS Code extension | `vscode-extension/` | Phase 4 |
