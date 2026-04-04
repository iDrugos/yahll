# Yahll

> Your personal self-evolving AI coding agent. Zero tokens. Fully local. Always learning.

Built by Drugos. Powered by Ollama + qwen2.5-coder:7b.

## Quick Start

```bash
yahll          # start interactive session
yahll "fix this bug in main.py"   # one-shot query
```

## Commands

| Command | Description |
|---------|-------------|
| `/status` | Version + last session |
| `/history` | All saved patches |
| `/memory` | What Yahll knows about you |
| `/upgrade` | Yahll improves itself |
| `/model qwen2.5-coder:7b` | Switch model |
| `/clear` | Clear session |
| `/help` | All commands |

## Project Structure

```
Yahll Project/
├── src/           ← source code
├── docs/specs/    ← design documents
├── patches/       ← patch notes per version
└── README.md
```

## Patch Notes

See [patches/PATCH-NOTES.md](patches/PATCH-NOTES.md)
