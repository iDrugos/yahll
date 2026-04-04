---
name: yahll-memory
description: Use when working on Yahll's memory/patch system — explains how sessions are saved, loaded, and injected into context so Yahll always knows where it left off.
---

# Yahll Memory System

## Overview

Every Yahll session is saved as a JSON patch file. On next launch, the latest patch is loaded and injected into the system prompt, so Yahll always has context from the previous session.

## Storage Locations

```
~/.yahll/sessions/          ← primary (loaded on startup)
    2026-04-04-143022.json
    2026-04-04-150511.json

Desktop/Yahll Project/patches/   ← backup + visible to user
    session-2026-04-04-143022.json
    PATCH-NOTES.md
```

## Patch File Format

```json
{
  "timestamp": "2026-04-04T14:30:22.123456",
  "summary": "Built the Ollama client and ran first streaming test",
  "learned": [
    "user prefers Python over Rust",
    "project name is Yahll",
    "RTX 4070, 32GB RAM available",
    "model: qwen2.5-coder:7b"
  ],
  "files_changed": ["src/yahll/core/ollama_client.py"],
  "self_improvements": [],
  "next_context": "Continue with Task 3: Tools implementation",
  "model": "qwen2.5-coder:7b"
}
```

## Key Functions

### save_patch(data: dict)
- Adds `timestamp` field automatically
- Writes to `~/.yahll/sessions/TIMESTAMP.json`
- Called automatically on `/exit` or Ctrl+C

### load_latest_patch() → dict | None
- Returns most recent patch (sorted by filename = timestamp)
- Returns None if no sessions exist yet

### build_context_from_patch(patch: dict) → str
Converts patch to human-readable string:
```
Last session: 2026-04-04T14:30:22
Summary: Built the Ollama client and ran first streaming test
Known about user/project: user prefers Python over Rust, project name is Yahll
Continue from: Continue with Task 3: Tools implementation
```

### list_patches() → list[dict]
Returns all patches sorted oldest→newest, each with `"file"` key added.

## How Context is Injected

In `main.py → _make_agent()`:
```python
agent = Agent(model=config["model"])
patch = load_latest_patch()
if patch:
    context = build_context_from_patch(patch)
    agent.inject_context(context)  # appends to system prompt
```

In `agent.py → inject_context(context: str)`:
```python
self.messages[0]["content"] = SYSTEM_PROMPT + "\n\n" + context
```

## How to Improve the Summary

Currently the summary is just the first user message truncated.
Better approach (Phase 2): ask the model to summarize before saving:

```python
summary_response = agent.chat(
    "Summarize what we accomplished this session in 1-2 sentences. "
    "Also list 3-5 key facts you learned about the user or project."
)
# parse response into summary + learned list
```

## PATCH-NOTES.md Format

```markdown
## v0.1.0 — 2026-04-04
**Status:** Core agent working

### What's included
- feature 1
- feature 2

### Next phase
- what to do next
```

New entries are appended automatically after each session.
