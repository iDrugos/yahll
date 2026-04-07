"""
knowledge.md — persistent growing knowledge base across sessions.
Yahll appends key facts here so they survive indefinitely, not just one session.
"""
import os
from datetime import datetime

YAHLL_HOME = os.path.expanduser("~/.yahll")
KNOWLEDGE_PATH = os.path.join(YAHLL_HOME, "knowledge.md")

_HEADER = """# Yahll — Persistent Knowledge Base

This file grows across sessions. Yahll reads it on startup.
Each entry is a dated fact worth remembering long-term.

---

"""


def load_knowledge() -> str:
    """Return the full knowledge.md content, or empty string if none."""
    if not os.path.exists(KNOWLEDGE_PATH):
        return ""
    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def append_knowledge(facts: list[str]):
    """Append a list of new facts to knowledge.md."""
    if not facts:
        return
    os.makedirs(YAHLL_HOME, exist_ok=True)
    date = datetime.now().strftime("%Y-%m-%d")
    lines = [f"- [{date}] {fact}" for fact in facts if fact.strip()]
    if not lines:
        return

    if not os.path.exists(KNOWLEDGE_PATH):
        with open(KNOWLEDGE_PATH, "w", encoding="utf-8") as f:
            f.write(_HEADER)

    with open(KNOWLEDGE_PATH, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def get_knowledge_context() -> str:
    """Return compact knowledge for system prompt injection."""
    content = load_knowledge()
    if not content:
        return ""
    # Return last 30 lines to keep context size in check
    lines = [l for l in content.splitlines() if l.startswith("- [")]
    recent = lines[-30:] if len(lines) > 30 else lines
    if not recent:
        return ""
    return "Persistent knowledge:\n" + "\n".join(recent)
