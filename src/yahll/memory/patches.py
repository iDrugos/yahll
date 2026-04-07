import os
import json
import re
from datetime import datetime
from typing import Optional

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


def build_smart_summary(messages: list) -> dict:
    """Extract a meaningful summary and learned facts from conversation messages."""
    user_msgs = [
        m["content"] for m in messages
        if m["role"] == "user"
        and not m["content"].startswith("<result tool=")
        and not m["content"].startswith("[Tool:")
        and "Please summarize them for the user" not in m["content"]
    ]
    assistant_msgs = [m["content"] for m in messages if m["role"] == "assistant" and m.get("content")]

    # Build a short summary from all user messages (not just the first)
    topics = []
    for msg in user_msgs[:8]:  # cap at 8 to keep summary small
        stripped = msg.strip()[:80]
        if stripped:
            topics.append(stripped)

    summary_text = " | ".join(topics) if topics else "no topics"
    date_str = datetime.now().strftime("%Y-%m-%d")
    summary = f"Session {date_str} - {summary_text[:120]}"

    # Extract learned facts: files created, commands run, packages installed
    learned = []
    all_text = " ".join(user_msgs + assistant_msgs)

    # Detect installed packages
    pip_matches = re.findall(r"pip install ([\w\-]+)", all_text)
    for pkg in set(pip_matches):
        learned.append(f"installed: {pkg}")

    # Detect written files
    write_matches = re.findall(r"(?:wrote|created|saved|writing).{0,30}?([\w/\\:.]+\.(?:py|md|json|txt|pdf))", all_text, re.I)
    for path in set(write_matches[:5]):
        learned.append(f"created file: {path}")

    # Detect topics discussed
    if "pdf" in all_text.lower():
        learned.append("worked with PDFs")
    if "install" in all_text.lower():
        learned.append("installed software")
    if "error" in all_text.lower() or "fix" in all_text.lower():
        learned.append("debugged issues")

    # Last user message as next-session context
    next_context = user_msgs[-1][:120] if user_msgs else ""

    return {
        "summary": summary,
        "learned": learned or ["user: Drugos", "project: Yahll"],
        "next_context": next_context,
    }


def model_summarize_session(messages: list, base_url: str = "http://localhost:11434", model: str = "qwen2.5-coder:7b") -> Optional[dict]:
    """Ask Ollama to summarize the session. Returns {summary, learned} or None on failure."""
    try:
        import httpx

        # Build a condensed transcript of only user + assistant turns (no tool noise)
        transcript_lines = []
        for m in messages:
            role = m.get("role", "")
            content = m.get("content", "") or ""
            if role == "system":
                continue
            if role == "user" and (
                content.startswith("<result tool=") or
                content.startswith("[Tool:") or
                "Please summarize them for the user" in content
            ):
                continue
            if content.strip():
                transcript_lines.append(f"{role.upper()}: {content.strip()[:300]}")

        if not transcript_lines:
            return None

        transcript = "\n".join(transcript_lines[:40])  # cap at 40 turns

        summary_prompt = f"""Summarize this Yahll session in 1-2 sentences. Then list 3-5 specific facts worth remembering long-term (files created, packages installed, problems solved, user preferences).

Respond ONLY in this JSON format:
{{"summary": "one or two sentence summary", "learned": ["fact1", "fact2", "fact3"]}}

SESSION:
{transcript}"""

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": summary_prompt}],
            "stream": False,
        }
        response = httpx.post(f"{base_url}/api/chat", json=payload, timeout=60.0)
        response.raise_for_status()
        content = response.json().get("message", {}).get("content", "")

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        pass
    return None


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
