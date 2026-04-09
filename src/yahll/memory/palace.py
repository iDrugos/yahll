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
