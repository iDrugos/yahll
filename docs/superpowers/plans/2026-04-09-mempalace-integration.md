# MemPalace Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate MemPalace as Yahll's long-term memory library — verbatim ChromaDB storage of every session, semantic search via `/recall`, and automatic Layer 0+1 injection at startup.

**Architecture:** Install MemPalace as a git dependency. Wrap its API in `src/yahll/memory/palace.py` (init, load layers, mine session, search). Modify `main.py` to inject memory at startup, mine on exit, and handle `/recall`. Patches system unchanged.

**Tech Stack:** Python, ChromaDB (via MemPalace), mempalace (git dep), pytest, unittest.mock

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `pyproject.toml` | Modify | Add mempalace git dependency |
| `src/yahll/memory/palace.py` | Create | Wraps MemPalace: init, load_context, mine_session, search |
| `src/yahll/main.py` | Modify | Inject L0+L1 at startup, mine on exit, add `/recall` command |
| `tests/test_palace.py` | Create | Unit tests for palace.py with mocked ChromaDB |

---

## Task 1: Install MemPalace dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add mempalace to dependencies**

In `pyproject.toml`, find the `dependencies` list and add:

```toml
"mempalace @ git+https://github.com/milla-jovovich/mempalace.git",
```

Full dependencies block should look like:
```toml
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "httpx>=0.27.0",
    "pyyaml>=6.0",
    "pytest>=8.0.0",
    "mempalace @ git+https://github.com/milla-jovovich/mempalace.git",
]
```

- [ ] **Step 2: Install the dependency**

```bash
pip install -e .
```

Expected: installs mempalace + chromadb + sentence-transformers (may take 1-2 minutes on first run due to model download).

- [ ] **Step 3: Verify import works**

```bash
python -c "from mempalace.layers import Layer0, Layer1; from mempalace.searcher import search; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add mempalace as long-term memory dependency"
```

---

## Task 2: Create `palace.py` — MemPalace wrapper

**Files:**
- Create: `src/yahll/memory/palace.py`
- Create: `tests/test_palace.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_palace.py`:

```python
import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path


# --- init_palace ---

def test_init_palace_creates_directory(tmp_path):
    palace_dir = str(tmp_path / "yahll_palace")
    with patch("yahll.memory.palace.PALACE_PATH", palace_dir):
        from yahll.memory.palace import init_palace
        result = init_palace()
    assert os.path.isdir(palace_dir)
    assert result == palace_dir


# --- load_context ---

def test_load_context_returns_string():
    with patch("yahll.memory.palace.Layer0") as mock_l0, \
         patch("yahll.memory.palace.Layer1") as mock_l1:
        mock_l0.return_value.render.return_value = "## L0\nDrugos"
        mock_l1.return_value.generate.return_value = "## L1\nTop moments"
        from yahll.memory.palace import load_context
        result = load_context()
    assert "L0" in result
    assert "L1" in result


def test_load_context_returns_empty_on_error():
    with patch("yahll.memory.palace.Layer0", side_effect=Exception("no palace")):
        from yahll.memory.palace import load_context
        result = load_context()
    assert result == ""


# --- mine_session ---

def test_mine_session_stores_exchanges(tmp_path):
    palace_dir = str(tmp_path / "palace")
    os.makedirs(palace_dir)
    messages = [
        {"role": "system", "content": "You are Yahll."},
        {"role": "user", "content": "What is 2+2?"},
        {"role": "assistant", "content": "4"},
        {"role": "user", "content": "Thanks"},
        {"role": "assistant", "content": "You're welcome"},
    ]
    mock_col = MagicMock()
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_col

    with patch("yahll.memory.palace.PALACE_PATH", palace_dir), \
         patch("yahll.memory.palace.chromadb.PersistentClient", return_value=mock_client):
        from yahll.memory.palace import mine_session
        mine_session(messages)

    assert mock_col.upsert.called


def test_mine_session_skips_system_messages(tmp_path):
    palace_dir = str(tmp_path / "palace")
    os.makedirs(palace_dir)
    messages = [
        {"role": "system", "content": "System prompt"},
    ]
    mock_col = MagicMock()
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_col

    with patch("yahll.memory.palace.PALACE_PATH", palace_dir), \
         patch("yahll.memory.palace.chromadb.PersistentClient", return_value=mock_client):
        from yahll.memory.palace import mine_session
        mine_session(messages)

    mock_col.upsert.assert_not_called()


# --- search ---

def test_search_returns_results():
    mock_results = {
        "documents": [["You asked about 2+2", "We debugged agent.py"]],
        "metadatas": [[{"wing": "yahll"}, {"wing": "yahll"}]],
        "distances": [[0.1, 0.2]],
    }
    mock_col = MagicMock()
    mock_col.query.return_value = mock_results
    mock_client = MagicMock()
    mock_client.get_collection.return_value = mock_col

    with patch("yahll.memory.palace.chromadb.PersistentClient", return_value=mock_client):
        from yahll.memory.palace import search
        results = search("2+2")

    assert len(results) == 2
    assert "2+2" in results[0]


def test_search_returns_empty_on_no_palace():
    with patch("yahll.memory.palace.chromadb.PersistentClient", side_effect=Exception("no db")):
        from yahll.memory.palace import search
        results = search("anything")
    assert results == []
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
pytest tests/test_palace.py -v
```

Expected: `ImportError` — `palace` module does not exist yet.

- [ ] **Step 3: Create `src/yahll/memory/palace.py`**

```python
"""
palace.py — MemPalace wrapper for Yahll long-term memory.

The library: verbatim ChromaDB storage + semantic search across all sessions.
Runs alongside patches.py (short-term). Never replaces it.
"""

import hashlib
import os
import threading
from datetime import datetime
from pathlib import Path

import chromadb

from mempalace.layers import Layer0, Layer1

PALACE_PATH = os.path.expanduser("~/.mempalace/palace")
WING = "yahll"
COLLECTION = "mempalace_drawers"


def init_palace() -> str:
    """Ensure palace directory exists. Returns palace path."""
    Path(PALACE_PATH).mkdir(parents=True, exist_ok=True)
    return PALACE_PATH


def load_context() -> str:
    """
    Load Layer 0 (identity) + Layer 1 (top moments) for context injection.
    Returns formatted string, or empty string if palace is empty/missing.
    """
    try:
        l0 = Layer0().render()
        l1 = Layer1(palace_path=PALACE_PATH, wing=WING).generate()
        parts = []
        if l0 and "No identity configured" not in l0:
            parts.append(l0)
        if l1 and "No palace found" not in l1:
            parts.append(l1)
        return "\n\n".join(parts)
    except Exception:
        return ""


def mine_session(messages: list[dict]) -> None:
    """
    Store the session conversation verbatim in ChromaDB.
    Runs in a background thread — does not block session exit.
    Only stores user+assistant turns (skips system messages).
    """
    def _mine():
        try:
            exchanges = _extract_exchanges(messages)
            if not exchanges:
                return
            client = chromadb.PersistentClient(path=PALACE_PATH)
            col = client.get_or_create_collection(COLLECTION)
            now = datetime.now().isoformat()
            ids, docs, metas = [], [], []
            for i, (user_msg, assistant_msg) in enumerate(exchanges):
                content = f"USER: {user_msg}\nYAHLL: {assistant_msg}"
                uid = hashlib.md5(f"{now}-{i}-{content[:40]}".encode()).hexdigest()
                ids.append(uid)
                docs.append(content)
                metas.append({"wing": WING, "room": "session", "timestamp": now})
            col.upsert(ids=ids, documents=docs, metadatas=metas)
        except Exception:
            pass  # memory mining is best-effort, never crash the session

    threading.Thread(target=_mine, daemon=True).start()


def search(query: str, n: int = 5) -> list[str]:
    """
    Layer 3 semantic search across all Yahll sessions.
    Returns list of verbatim conversation excerpts.
    """
    try:
        client = chromadb.PersistentClient(path=PALACE_PATH)
        col = client.get_collection(COLLECTION)
        results = col.query(
            query_texts=[query],
            n_results=n,
            where={"wing": WING},
            include=["documents", "metadatas", "distances"],
        )
        return results["documents"][0]
    except Exception:
        return []


def _extract_exchanges(messages: list[dict]) -> list[tuple[str, str]]:
    """
    Pair up user+assistant messages into (user, assistant) tuples.
    Skips system messages and tool result messages.
    """
    exchanges = []
    i = 0
    non_system = [m for m in messages if m.get("role") != "system"]
    while i < len(non_system) - 1:
        msg = non_system[i]
        next_msg = non_system[i + 1]
        if msg.get("role") == "user" and next_msg.get("role") == "assistant":
            user_content = msg.get("content", "")
            assistant_content = next_msg.get("content", "")
            # Skip tool result messages (they're just JSON blobs)
            if user_content and not user_content.startswith("<result tool="):
                exchanges.append((user_content[:500], assistant_content[:500]))
            i += 2
        else:
            i += 1
    return exchanges
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/test_palace.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Run all tests — expect pass**

```bash
pytest tests/ -v
```

Expected: all tests pass (41 + 6 = 47 passed)

- [ ] **Step 6: Commit**

```bash
git add src/yahll/memory/palace.py tests/test_palace.py
git commit -m "feat: add palace.py — MemPalace wrapper for long-term memory"
```

---

## Task 3: Wire MemPalace into `main.py`

**Files:**
- Modify: `src/yahll/main.py`

- [ ] **Step 1: Add palace import**

At the top of `main.py`, after the existing memory imports, add:

```python
from yahll.memory.palace import init_palace, load_context, mine_session, search as palace_search
```

- [ ] **Step 2: Inject L0+L1 at startup**

Find the `_make_agent()` function. It currently builds a `parts` list and injects context. Add palace context to that list:

```python
def _make_agent(config: dict) -> Agent:
    agent = Agent(model=config["model"], base_url=config["ollama_url"])

    # Build combined context: identity + knowledge + palace L0+L1 + last session patch
    parts = [get_identity_context()]
    knowledge = get_knowledge_context()
    if knowledge:
        parts.append(knowledge)

    # MemPalace: Layer 0 (identity) + Layer 1 (top moments)
    palace_ctx = load_context()
    if palace_ctx:
        parts.append(f"## LONG-TERM MEMORY (MemPalace)\n{palace_ctx}")

    patch = load_latest_patch()
    if patch:
        parts.append(build_context_from_patch(patch))
    agent.inject_context("\n\n".join(parts))

    return agent
```

- [ ] **Step 3: Initialize palace at startup**

In the `main()` function, after `config = load_config()` and before `_make_agent()`, add:

```python
    init_palace()
```

- [ ] **Step 4: Mine session on exit**

In `_save_session()`, at the very end after `save_patch(patch_data)`, add:

```python
    mine_session(agent.messages)
```

To do this, `_save_session()` needs access to `agent`. Find the current signature:

```python
def _save_session(agent: Agent, config: dict):
```

It already takes `agent` — just add the mine call at the end:

```python
    save_patch(patch_data)
    _save_to_project(patch_data)
    mine_session(agent.messages)  # store verbatim in MemPalace (background thread)
```

- [ ] **Step 5: Add `/recall` command**

In `_handle_slash_command()`, add before the `/clear` block:

```python
    if command == "/recall":
        query = " ".join(parts[1:]).strip()
        if not query:
            console.print("  [dim]Usage: /recall <what you want to find>[/dim]")
            return True
        console.print(f"\n  [bold cyan]RECALL[/bold cyan]  [dim cyan]── \"{query}\"[/dim cyan]")
        console.print(Rule(style="cyan dim"))
        with console.status("  [dim cyan]SEARCHING PALACE...[/dim cyan]", spinner="dots"):
            results = palace_search(query, n=5)
        if not results:
            console.print("  [dim]No memories found.[/dim]")
        else:
            for i, excerpt in enumerate(results, 1):
                console.print(f"  [dim cyan][{i}][/dim cyan] {excerpt[:300]}")
                console.print()
            console.print(Rule(style="cyan dim"))
            console.print(f"  [dim]{len(results)} memories recalled.[/dim]\n")
            # Inject results into agent context
            agent.inject_context(
                f"RECALLED MEMORIES for '{query}':\n" + "\n---\n".join(results)
            )
        return True
```

Note: `_handle_slash_command` already takes `agent` as a parameter so this works directly.

- [ ] **Step 6: Add `/recall` to `/help`**

Find the `cmds` list in the `/help` handler and add:

```python
("/recall QUERY",  "search long-term memory palace"),
```

Add it after the `/memory` entry.

- [ ] **Step 7: Run all tests**

```bash
pytest tests/ -v
```

Expected: all 47 tests pass (palace tests mock ChromaDB so no real DB needed).

- [ ] **Step 8: Commit**

```bash
git add src/yahll/main.py
git commit -m "feat: wire MemPalace into Yahll — L0+L1 injection at startup, mine on exit, /recall command"
```

---

## Task 4: Create MemPalace identity file + smoke test

**Files:**
- Create: `~/.mempalace/identity.txt` (on user's machine, not in repo)

- [ ] **Step 1: Create identity.txt**

Create `~/.mempalace/identity.txt` with:

```
I am Yahll, a self-evolving local AI coding agent built by Drugos.
I run 100% locally via Ollama — zero tokens, zero cost.
My owner is Drugos, a developer building local AI tools.
Hardware: ASUS ROG Strix G814JI, Intel i9-13980HX, 32GB RAM, RTX 4070 Laptop 8GB VRAM.
Project: Yahll — a self-evolving local AI coding agent CLI.
```

- [ ] **Step 2: Smoke test — run yahll**

```bash
yahll
```

Expected boot sequence completes, no errors.

- [ ] **Step 3: Send a message and exit**

Type any message, get a response, then type `/exit`.
Expected: session saved to patches AND mined into MemPalace (background, silent).

- [ ] **Step 4: Test `/recall`**

Start a new session:
```bash
yahll
> /recall what did we build
```

Expected: excerpts from previous session appear.

- [ ] **Step 5: Update Yahll.md**

Mark Phase 5 complete. Add session entry.

- [ ] **Step 6: Push to GitHub**

```bash
git push origin main
```
