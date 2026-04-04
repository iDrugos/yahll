# Yahll — Self-Evolving AI Coding Agent
**Spec Date:** 2026-04-04  
**Status:** Approved  
**Author:** Drugos + Claude  

---

## Vision

Yahll is a personal AI coding agent that runs entirely locally (zero API tokens, zero cost), learns from every session, and continuously improves itself. It lives in the terminal as `yahll`, knows who it is, remembers past conversations via patch files, and can upgrade its own capabilities on demand.

---

## Core Principles

1. **Zero tokens** — powered by Ollama local LLM (qwen2.5-coder:7b on RTX 4070)
2. **Persistent identity** — every session is saved as a patch; Yahll always knows its history
3. **Self-improving** — Yahll can read, modify, and upgrade its own source code
4. **Offline first** — works with no internet connection after initial model download

---

## Architecture

### Directory Structure

```
~/.yahll/                          ← Yahll home (installed globally)
    ├── yahll.py                   ← entry point / main loop
    ├── core/
    │   ├── agent.py               ← conversation loop + tool dispatch
    │   ├── ollama_client.py       ← HTTP client for Ollama API
    │   └── config.py              ← load/save config.yaml
    ├── tools/
    │   ├── bash.py                ← execute shell commands
    │   ├── files.py               ← read / write / edit files
    │   ├── search.py              ← grep and find in codebase
    │   └── self_tools.py          ← read/modify Yahll's own source
    ├── memory/
    │   ├── identity.md            ← "I am Yahll v0.x, I know..."
    │   ├── knowledge.md           ← accumulated learnings across sessions
    │   └── sessions/              ← one JSON patch per session
    │       ├── 2026-04-04-001.json
    │       └── ...
    ├── patches/                   ← full snapshots at each version
    │   ├── v0.1.0/
    │   └── v0.2.0/
    └── config.yaml                ← model name, settings, user preferences

Desktop/Yahll Project/             ← project source + patch notes (this folder)
    ├── docs/specs/                ← design documents
    ├── patches/                   ← patch notes per version
    ├── src/                       ← source code
    └── README.md
```

---

## Components

### 1. CLI Entry Point
- Command: `yahll` in any terminal
- Supports: interactive REPL mode and single-query mode
- Installed via `pip install -e .` from project source

### 2. Conversation Loop (agent.py)
- Sends user message + context to Ollama
- Parses tool calls from model response
- Executes tools, feeds results back to model
- Loops until model returns final answer (no more tool calls)

### 3. Ollama Client (ollama_client.py)
- HTTP calls to `http://localhost:11434`
- Supports streaming responses
- Compatible with OpenAI API format
- Default model: `qwen2.5-coder:7b`

### 4. Tools

| Tool | What it does |
|------|-------------|
| `bash_execute` | Run any shell command, return output |
| `read_file` | Read file contents with line numbers |
| `write_file` | Create or overwrite a file |
| `edit_file` | Replace specific string in a file |
| `search_files` | Grep for pattern across files |
| `list_directory` | List files and folders |
| `self_read` | Read Yahll's own source files |
| `self_write` | Modify Yahll's own source files |

### 5. Memory & Patches

Every session ends with an auto-saved patch file:

```json
{
  "session_id": "2026-04-04-001",
  "timestamp": "2026-04-04T14:30:00",
  "summary": "Built the initial CLI skeleton",
  "user_preferences": ["prefers Python", "project = Yahll"],
  "learned": ["RTX 4070 available", "32GB RAM"],
  "files_changed": ["src/core/agent.py"],
  "self_improvements": [],
  "next_context": "Continue building tool system"
}
```

On startup, Yahll reads the latest patch and resumes with full context.

### 6. Self-Upgrade System

Yahll can modify its own code:
1. User requests a new capability (e.g., "add web search")
2. Yahll reads its own source via `self_read`
3. Writes improved code via `self_write`
4. Runs tests to verify
5. Saves a version snapshot to `patches/vX.Y.Z/`
6. Updates `identity.md` with new version info

---

## Slash Commands

| Command | Action |
|---------|--------|
| `/yahll` | Start the agent |
| `/status` | Current version + last session summary |
| `/history` | List all saved patches |
| `/memory` | Show what Yahll knows about user and project |
| `/upgrade` | Yahll proposes and applies self-improvements |
| `/model <name>` | Switch to a different Ollama model |
| `/clear` | Clear current session context |
| `/help` | List all commands |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| CLI framework | Typer + Rich (colored output) |
| LLM | Ollama (qwen2.5-coder:7b) |
| Tool calling | JSON schema function dispatch |
| Memory | JSON + Markdown files |
| Versioning | Git patches + file snapshots |
| Testing | pytest |
| VS Code (Phase 4) | TypeScript extension |

---

## Hardware

- **Machine:** ASUS ROG Strix G814JI
- **CPU:** Intel i9-13980HX (24 cores)
- **RAM:** 32 GB
- **GPU:** NVIDIA RTX 4070 Laptop (8GB VRAM)
- **Model:** qwen2.5-coder:7b (~5GB VRAM) — runs comfortably

---

## Development Phases

### Phase 1 — Core Agent (Week 1)
- Project scaffold + CLI entry point
- Ollama client with streaming
- Basic REPL loop
- Tools: bash, read, write, search, list

### Phase 2 — Memory & Patches (Week 2)
- Auto-save session patches
- Load latest patch on startup
- identity.md + knowledge.md
- `/history`, `/memory`, `/status` commands

### Phase 3 — Self-Upgrade (Week 3)
- self_read + self_write tools
- Version snapshot system
- `/upgrade` command
- Yahll improves itself

### Phase 4 — VS Code Extension (Future)
- Extension scaffold (TypeScript)
- Sidebar chat panel
- Inline code suggestions
- `/yahll` in Command Palette

---

## Success Criteria

- [ ] `yahll` command works from any terminal directory
- [ ] Ollama responds with streaming output
- [ ] All 8 tools functional and tested
- [ ] Session patches saved automatically
- [ ] On restart, Yahll knows last session context
- [ ] `/upgrade` successfully modifies and re-saves Yahll's own code
- [ ] Zero external API calls (fully local)
