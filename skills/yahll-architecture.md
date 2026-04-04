---
name: yahll-architecture
description: Use when working on any part of Yahll — explains the full architecture, data flow, and component responsibilities so you never get lost.
---

# Yahll Architecture

## Overview

Yahll is a local AI coding agent. User types in terminal → CLI → Agent loop → Ollama LLM → Tools → Response.
Everything runs locally. Zero external API calls. Zero tokens consumed.

## Data Flow

```
User input
    │
    ▼
main.py (CLI)
    │  slash commands handled here (/help /status /upgrade etc.)
    │
    ▼
agent.py (Agent.chat)
    │  builds message list, calls Ollama, dispatches tools in loop
    │
    ├──► ollama_client.py ──► Ollama HTTP API (localhost:11434)
    │         streaming response (JSON chunks)
    │
    ├──► tools/registry.py ──► dispatch(name, args)
    │         │
    │         ├── bash.py        bash_execute(command)
    │         ├── files.py       read_file / write_file / edit_file
    │         ├── search.py      search_files / list_directory
    │         └── self_tools.py  self_read / self_write / self_list
    │
    ▼
memory/patches.py
    │  save_patch() called on session end
    │  load_latest_patch() called on session start
    ▼
~/.yahll/sessions/TIMESTAMP.json
```

## Key Components

### main.py
- Entry point for `yahll` command
- Two modes: interactive REPL and single-query
- Handles all slash commands
- Calls `_save_session_patch()` on exit
- Calls `_make_agent()` which loads memory context

### agent.py — Agent class
- `messages: list[dict]` — full conversation history
- `chat(user_message)` → loops until no more tool calls → returns string
- Tool call loop: model returns tool_calls → dispatch → add result → re-send to model
- `inject_context(str)` — appends memory to system prompt
- `clear()` — resets messages, keeps system prompt

### ollama_client.py — OllamaClient class
- `chat_stream(messages, tools)` → yields JSON chunks
- `is_running()` → health check before starting
- `list_models()` → available local models

### tools/registry.py
- `TOOL_SCHEMAS` — list of JSON schema dicts for Ollama
- `TOOL_DISPATCH` — dict mapping name → function
- `dispatch(name, args)` → calls the right function

### memory/patches.py
- `save_patch(data)` — writes JSON to `~/.yahll/sessions/`
- `load_latest_patch()` — reads most recent JSON
- `build_context_from_patch(patch)` — converts patch to string for system prompt

## Tool Call Loop Detail

```python
while True:
    stream response from Ollama
    if response has tool_calls:
        add assistant message
        for each tool_call:
            result = dispatch(name, args)
            add tool result message
        continue loop (send results back to model)
    else:
        add assistant message
        return content  # final answer
```

## Memory System

On startup:
1. `load_latest_patch()` → get last session JSON
2. `build_context_from_patch()` → convert to string
3. `agent.inject_context()` → prepend to system prompt

On shutdown:
1. Build patch dict with summary, learned, next_context
2. `save_patch()` → write to `~/.yahll/sessions/TIMESTAMP.json`
3. Also write to `Desktop/Yahll Project/patches/session-TIMESTAMP.json`
4. Append entry to `patches/PATCH-NOTES.md`

## Config

Location: `~/.yahll/config.yaml`

```yaml
model: qwen2.5-coder:7b
ollama_url: http://localhost:11434
max_context_messages: 50
auto_save_patches: true
```

Loaded by `config.py` at startup. Defaults created if missing.
