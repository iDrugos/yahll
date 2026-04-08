# Yahll VS Code Extension — Design Spec
**Date:** 2026-04-08  
**Phase:** 4  
**Status:** Approved

---

## Overview

A VS Code extension that brings Yahll into the editor. It has two parts:

1. **Setup Wizard** — runs automatically on first install, guides the user through installing Ollama, selecting and pulling the best AI model for their hardware, and initializing Yahll. Terminal-style, JARVIS aesthetic.
2. **Chat Panel** — a sidebar WebviewPanel with streaming Yahll chat and full slash command support.

---

## Part 1: Setup Wizard

### Behavior

- Triggers automatically the **first time VS Code opens** after the extension is installed.
- Detects if setup has already completed (checks `~/.yahll/setup_complete` flag file) and skips on subsequent launches.
- Runs as a Python script (`src/yahll/setup.py`) launched in the **VS Code integrated terminal** by the extension.
- After setup completes, the chat panel opens automatically.

### Steps

```
1. SCANNING HOST ARCHITECTURE
   - Detect CPU name + core count (platform / wmic)
   - Detect RAM (psutil)
   - Detect GPU name + VRAM (nvidia-smi or wmic)

2. LOCATING OLLAMA RUNTIME
   - Check if `ollama` is on PATH
   - If not: download and install via winget (Windows) / brew (Mac) / apt (Linux)
   - Verify with `ollama --version`

3. NEURAL MODEL SELECTION PROTOCOL
   - Select best model based on detected VRAM:
     | VRAM       | Model                  |
     |------------|------------------------|
     | >= 8 GB    | qwen2.5-coder:7b       |
     | 4–8 GB     | qwen2.5-coder:3b       |
     | < 4 GB     | qwen2.5-coder:1.5b     |
     | No GPU     | qwen2.5-coder:1.5b     |
   - Pull model with `ollama pull <model>` — show live progress bar

4. BINDING YAHLL TO LOCAL INTELLIGENCE
   - Write selected model to `~/.yahll/config.yaml`
   - Write `~/.yahll/setup_complete` flag
   - Confirm Ollama is running (`ollama serve` if not)

5. DONE — print "YAHLL IS ONLINE. GOOD MORNING, <username>."
```

### Aesthetic

JARVIS / Tony Stark terminal style using Rich:
- ASCII banner at top
- Each step prefixed with `>`
- Dot-padded key/value lines: `CPU ........... Intel i9-13980HX [32 CORES DETECTED]`
- Spinner (`⠸`) while working, `✓` on success, `⚠` on warning
- Progress bar for downloads: `[██████████░░░░░░░░░░] 54%`
- Final line in bold cyan: `[ YAHLL IS ONLINE. GOOD MORNING, DRUGOS. ]`

### Files

| File | Action |
|------|--------|
| `src/yahll/setup.py` | Python setup wizard script |

---

## Part 2: Chat Panel

### Architecture

```
VS Code Extension (TypeScript)
  ├── extension.ts        — activates, registers command, manages WebviewPanel + subprocess
  └── webview/
      └── chat.html       — chat UI (HTML/CSS/JS, dark JARVIS theme)

Yahll CLI (Python)
  └── main.py             — new --pipe flag: disables Rich ANSI, flushes per chunk
```

### Data Flow

```
User types in webview input
  → postMessage("send", text) → extension.ts
    → write text + "\n" to yahll stdin
      → yahll streams stdout chunks
        → extension reads chunks line-by-line
          → postMessage("chunk", text) → webview
            → appended live to current chat bubble
```

### Subprocess

- Extension spawns `yahll --pipe` once on panel open.
- Single persistent process for the full VS Code session.
- On panel close: process is killed.
- On restart: new process spawned.
- `--pipe` flag in `main.py`: wraps output with `sys.stdout.flush()` after each chunk, strips Rich Console formatting (plain `print()` instead of `console.print()`).

### Chat Panel UI

Dark terminal aesthetic matching the setup wizard:
- Background: `#0d0d0d`, text: `#00ff9f` (cyan-green)
- Monospace font throughout
- Header bar: `YAHLL  ●  <model name>`
- Message history: user messages right-aligned in dimmer color, Yahll messages left-aligned in bright green
- Streaming: text appended character-by-character to current bubble
- Input box at bottom: full-width, dark, monospace — supports slash commands
- Slash commands pass through to Yahll unchanged (`/upgrade`, `/memory`, `/status`, `/clear`, etc.)

### Extension Manifest

```json
{
  "name": "yahll",
  "displayName": "Yahll — Local AI Agent",
  "activationEvents": ["onStartupFinished"],
  "contributes": {
    "commands": [{ "command": "yahll.openPanel", "title": "Yahll: Open Chat" }],
    "viewsContainers": { "activitybar": [{ "id": "yahll", "title": "Yahll" }] }
  }
}
```

### Files

| File | Action |
|------|--------|
| `vscode-extension/package.json` | Extension manifest |
| `vscode-extension/extension.ts` | Host: panel + subprocess + message bridge |
| `vscode-extension/webview/chat.html` | Chat UI |
| `vscode-extension/tsconfig.json` | TypeScript config |
| `src/yahll/main.py` | Add `--pipe` flag |

---

## Yahll CLI Changes

### `--pipe` flag in `main.py`

```python
@app.command()
def main(pipe: bool = typer.Option(False, "--pipe")):
    ...
```

When `--pipe` is active:
- Use plain `print()` instead of `console.print()` (no Rich ANSI codes)
- `sys.stdout.flush()` after every output line
- Slash commands still work identically

---

## Testing

- `src/yahll/setup.py`: manual smoke test — run on a clean machine or VM
- `extension.ts`: manual test — install extension, open VS Code, verify panel opens, verify streaming works, verify `/upgrade` runs the pipeline
- No automated tests for the extension itself (TypeScript unit tests are out of scope for Phase 4)

---

## What This Is NOT

- No cloud, no external APIs
- No VS Code Language Server Protocol
- No separate HTTP server added to Yahll
- No extension marketplace publish (local install only, for now)
