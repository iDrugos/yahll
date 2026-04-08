# YAHLL — Local AI Coding Agent

```
 ██╗   ██╗ █████╗ ██╗  ██╗██╗     ██╗
 ╚██╗ ██╔╝██╔══██╗██║  ██║██║     ██║
  ╚████╔╝ ███████║███████║██║     ██║
   ╚██╔╝  ██╔══██║██╔══██║██║     ██║
    ██║   ██║  ██║██║  ██║███████╗███████╗
    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝
```

> Your personal self-evolving AI coding agent. Zero tokens. Fully local. Always learning.

Works exactly like Claude Code — but runs 100% on **your machine** via Ollama.  
No API keys. No subscriptions. No data leaving your PC.

---

## What it does

- Reads and writes files, runs bash commands, searches your codebase
- Remembers every session and builds a knowledge base about you
- Improves its own code with `/upgrade` — runs tests, commits on success, rolls back on failure
- VS Code extension with a live streaming JARVIS-style chat panel
- Auto-selects the best AI model for your hardware on first install

---

## Requirements

- Python 3.11+
- Windows / macOS / Linux
- GPU with 4GB+ VRAM recommended (works on CPU too, just slower)

---

## Install

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/yahll.git
cd yahll

# 2. Install Python package
pip install -e .

# 3. Run setup wizard (installs Ollama + picks best model for your hardware)
python -m yahll.setup
```

The setup wizard auto-detects your GPU/VRAM and pulls the right model:

| VRAM | Model |
|------|-------|
| 8 GB+ | qwen2.5-coder:7b |
| 4–8 GB | qwen2.5-coder:3b |
| < 4 GB | qwen2.5-coder:1.5b |

---

## Use

```bash
yahll                          # interactive REPL
yahll "explain this file"      # one-shot query
yahll --model llama3.2:3b      # different model
```

---

## Commands

| Command | What it does |
|---------|-------------|
| `/help` | All commands |
| `/upgrade` | Yahll reads its own code, finds an improvement, applies it, runs tests, commits |
| `/memory` | What Yahll knows about you and your projects |
| `/status` | Version + last session |
| `/history` | All saved sessions |
| `/model NAME` | Switch Ollama model |
| `/clear` | Clear session context |
| `/exit` | Quit and save session |

---

## VS Code Extension

Install the extension for a JARVIS-style chat panel inside VS Code:

```bash
cd vscode-extension
npm install
npx tsc -p .
npx vsce package --allow-missing-repository --skip-license
code --install-extension yahll-*.vsix
```

Then reload VS Code and run **"Yahll: Open Chat"** from the command palette.

---

## How it works

```
yahll/
├── src/yahll/
│   ├── main.py               ← CLI entry point + REPL
│   ├── core/
│   │   ├── agent.py          ← conversation loop + tool dispatch
│   │   └── ollama_client.py  ← streaming Ollama HTTP client
│   ├── tools/
│   │   ├── registry.py       ← all tools registered here
│   │   ├── bash.py           ← bash_execute
│   │   ├── files.py          ← read/write/edit files
│   │   └── web_search.py     ← DuckDuckGo search
│   ├── memory/
│   │   ├── patches.py        ← session save/load
│   │   ├── knowledge.py      ← persistent fact base
│   │   ├── snapshots.py      ← source snapshot for safe self-upgrade
│   │   └── upgrades.py       ← test runner + git commit helper
│   └── setup.py              ← JARVIS-style first-run wizard
└── vscode-extension/         ← VS Code extension
```

---

## Self-upgrade safety

When you run `/upgrade`:
1. Snapshot of all source files taken in memory
2. Model reads its own code and proposes one improvement
3. Model applies the change (one file only)
4. `pytest` runs — if any test fails, snapshot is restored and nothing is committed
5. On success: version bumped, git commit created automatically

---

Built by **Drugos** — powered by [Ollama](https://ollama.com)
