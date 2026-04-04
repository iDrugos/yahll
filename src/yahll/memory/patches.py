import os
import json
from datetime import datetime

YAHLL_HOME = os.path.expanduser("~/.yahll")
SESSIONS_DIR = os.path.join(YAHLL_HOME, "sessions")


def save_patch(data: dict):
    """Save a session patch file with timestamp in filename."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    path = os.path.join(SESSIONS_DIR, f"{timestamp}.json")
    data["timestamp"] = datetime.now().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_latest_patch() -> dict | None:
    """Load the most recent session patch. Returns None if no patches exist."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    files = sorted([f for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")])
    if not files:
        return None
    with open(os.path.join(SESSIONS_DIR, files[-1]), "r", encoding="utf-8") as f:
        return json.load(f)


def list_patches() -> list[dict]:
    """Return all patches sorted oldest→newest."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    files = sorted([f for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")])
    patches = []
    for fname in files:
        with open(os.path.join(SESSIONS_DIR, fname), "r", encoding="utf-8") as f:
            patches.append({"file": fname, **json.load(f)})
    return patches


def build_context_from_patch(patch: dict) -> str:
    """Convert a patch into a context string for the system prompt."""
    lines = [
        f"Last session: {patch.get('timestamp', 'unknown')}",
        f"Summary: {patch.get('summary', 'no summary')}",
    ]
    learned = patch.get("learned", [])
    if learned:
        lines.append("Known about user/project: " + ", ".join(learned))
    next_ctx = patch.get("next_context", "")
    if next_ctx:
        lines.append(f"Continue from: {next_ctx}")
    return "\n".join(lines)
