# MemPalace Integration — Design Spec
**Date:** 2026-04-09
**Phase:** 5
**Status:** Approved

---

## Overview

Integrate MemPalace (96.6% LongMemEval, ChromaDB-backed verbatim memory) into Yahll as a long-term memory library running **alongside** the existing patch system.

- **Patches** = short-term memory (quick session resume, last summary)
- **MemPalace** = the library (everything ever said, forever, semantically searchable)

---

## Architecture

```
STARTUP
  patches.py       → load last session summary (unchanged)
  palace.py L0+L1  → identity + top moments injected into agent context

DURING SESSION
  agent context window holds all of the above + live conversation

ON COMMAND: /recall <query>
  palace.py L3     → semantic ChromaDB search, results printed + injected

SESSION END
  patches.py       → save summary (unchanged)
  palace.py        → mine full conversation into ChromaDB
```

**Palace location:** `~/.mempalace/yahll/`

---

## Dependencies

Add to `pyproject.toml`:
```toml
"mempalace @ git+https://github.com/milla-jovovich/mempalace.git",
```

MemPalace brings ChromaDB + sentence-transformers for local vector embeddings — no external API needed.

---

## New File: `src/yahll/memory/palace.py`

Single module that wraps all MemPalace interactions:

### `init_palace() -> str`
Ensures `~/.mempalace/yahll/` exists and ChromaDB collection is initialized. Returns palace path.

### `load_context() -> str`
Loads Layer 0 (identity, ~100 tokens) + Layer 1 (top moments, ~800 tokens).
Returns a formatted string ready to inject into agent context.
Returns empty string if palace is empty (first run).

### `mine_session(messages: list[dict]) -> None`
Takes the full agent message list, extracts user+assistant turns, passes to MemPalace miner.
Runs in a background thread so it doesn't block session exit.

### `search(query: str, n: int = 5) -> list[str]`
Layer 3 semantic search. Returns list of verbatim conversation excerpts.
Each result prefixed with metadata (approximate date, relevance).

---

## Changes to `src/yahll/main.py`

### Startup — inject L0+L1
```python
from yahll.memory.palace import init_palace, load_context
palace_path = init_palace()
palace_ctx = load_context()
if palace_ctx:
    parts.append(palace_ctx)
```
Added inside `_make_agent()` alongside existing identity + knowledge injection.

### Session end — mine conversation
```python
from yahll.memory.palace import mine_session
mine_session(agent.messages)  # runs in background thread
```
Added at the end of `_save_session()`.

### New command: `/recall <query>`
```python
if command == "/recall":
    query = " ".join(parts[1:])
    results = search(query)
    # print results, inject into agent context
```
Added to `_handle_slash_command()`. Listed in `/help`.

---

## `/recall` Output Format

```
  RECALL ── "how did we fix the tool parsing bug"
  ────────────────────────────────────────────────
  [1] session ~2026-04-07
      ...you: the tool calls weren't being parsed from qwen's response...
      ...yahll: I added _TOOL_CALL_TAG_RE to catch the <tool_call> format...

  [2] session ~2026-04-05
      ...relevant excerpt...
  ────────────────────────────────────────────────
  5 memories recalled. Injected into context.
```

---

## Testing

- `tests/test_palace.py` — unit tests for `init_palace`, `load_context`, `search`, `mine_session`
- Mock ChromaDB client in tests (no real DB needed)
- Manual smoke test: run 2 sessions, verify `/recall` returns content from both

---

## What This Is NOT

- No replacement of patches — both systems run in parallel
- No cloud, no external API — ChromaDB runs locally, embeddings via local sentence-transformers
- No UI changes — purely a backend memory upgrade
- No changes to the VS Code extension (it benefits automatically via `yahll --pipe`)
