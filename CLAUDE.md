# Yahll Project — Claude Code Context

## What is this project?

Yahll is a self-evolving local AI coding agent CLI built by Drugos.
It works exactly like Claude Code (`/claude`) but runs 100% locally via Ollama — zero tokens, zero cost.
The command will be `yahll` in any terminal.

## Hardware
- ASUS ROG Strix G814JI
- Intel i9-13980HX (24 cores / 32 threads)
- 32GB RAM
- NVIDIA RTX 4070 Laptop (8GB VRAM)
- Windows 11 Pro

## Tech Stack
- Python 3.11+
- Typer + Rich (CLI/REPL)
- httpx (HTTP client)
- Ollama local LLM (qwen2.5-coder:7b — default model)
- pytest (testing)

## Project Structure

```
Yahll Project/
├── CLAUDE.md               ← you are here
├── Yahll.md                ← living progress tracker
├── README.md
├── pyproject.toml          ← pip install -e . → activates `yahll` command
├── src/
│   └── yahll/
│       ├── main.py         ← CLI entry point (typer app)
│       ├── core/
│       │   ├── agent.py          ← conversation loop + tool dispatch
│       │   ├── ollama_client.py  ← streaming HTTP client for Ollama
│       │   └── config.py         ← ~/.yahll/config.yaml
│       ├── tools/
│       │   ├── registry.py       ← all tool schemas + dispatch
│       │   ├── bash.py           ← bash_execute
│       │   ├── files.py          ← read_file, write_file, edit_file
│       │   ├── search.py         ← search_files, list_directory
│       │   └── self_tools.py     ← self_read, self_write, self_list
│       └── memory/
│           ├── patches.py        ← save/load session JSON patches
│           └── identity.py       ← load identity.md + knowledge.md
├── tests/
│   ├── test_ollama_client.py
│   ├── test_tools.py
│   ├── test_agent.py
│   └── test_patches.py
├── docs/
│   ├── specs/2026-04-04-yahll-design.md        ← full design spec
│   └── superpowers/plans/
│       └── 2026-04-04-yahll-implementation.md  ← step-by-step plan
├── patches/
│   ├── PATCH-NOTES.md      ← version history
│   └── session-*.json      ← auto-saved session patches
└── skills/
    ├── yahll-architecture.md
    ├── yahll-tools.md
    └── yahll-memory.md
```

## How to Run

```bash
# Install (one time)
cd "C:/Users/Drugos-Laptop/Desktop/Yahll Project"
pip install -e .

# Start Ollama (must be running)
ollama serve

# Use Yahll
yahll                          # interactive REPL
yahll "explain this file"      # single query
yahll --model llama3.2:3b      # different model
```

## Slash Commands

| Command | Description |
|---------|-------------|
| `/help` | list all commands |
| `/status` | version + last session |
| `/history` | all saved session patches |
| `/memory` | what Yahll knows |
| `/model NAME` | switch Ollama model |
| `/upgrade` | Yahll improves itself |
| `/clear` | clear session context |
| `/exit` | quit + save patch |

## Development Phases

- **Phase 1** — Core agent (CLI + Ollama + tools + REPL) ← IN PROGRESS
- **Phase 2** — Memory & patches (auto-save, resume context)
- **Phase 3** — Self-upgrade (Yahll modifies own code)
- **Phase 4** — VS Code extension

## Key Decisions

- **Zero tokens**: Ollama local, no external API calls ever
- **Self-evolving**: Yahll has self_read/self_write tools to modify itself
- **Patch system**: every session saved as JSON, loaded on next launch
- **Python first**: Rust rewrite possible later for performance

## Important Files to Know

- `src/yahll/core/agent.py` — the brain: conversation loop + tool dispatch
- `src/yahll/tools/registry.py` — all tools registered here
- `src/yahll/memory/patches.py` — session persistence
- `src/yahll/main.py` — CLI entry point, all slash commands
- `Yahll.md` — always check this for current progress

## Testing

```bash
pytest tests/ -v              # run all tests
pytest tests/test_agent.py -v # specific file
```

## When Continuing Work

1. Read `Yahll.md` first — it shows exactly where we left off
2. Check `patches/PATCH-NOTES.md` for version history
3. Follow the plan in `docs/superpowers/plans/2026-04-04-yahll-implementation.md`
4. After each task: update `Yahll.md` with what was completed

---

## Skills Available

### Yahll-Specific Skills (`skills/`)

| Skill | When to use |
|-------|------------|
| `skills/superpowers/session-start.md` | **START OF EVERY SESSION** — orientation protocol |
| `skills/yahll-architecture.md` | Understanding component connections and data flow |
| `skills/yahll-tools.md` | Adding/modifying tools, tool signatures, registration |
| `skills/yahll-memory.md` | Memory/patch system, session persistence |
| `skills/superpowers/tdd.md` | Before writing any implementation code |
| `skills/superpowers/debugging.md` | When something breaks |
| `skills/superpowers/self-upgrade.md` | When running /upgrade or Yahll self-modifies |
| `skills/superpowers/new-feature.md` | Adding any new feature end-to-end |

### Knowledge Skills (`skills/knowledge/`)

| Skill | When to use |
|-------|------------|
| `skills/knowledge/llms-from-scratch.md` | Building GPT/transformer internals for Yahll's own LLM (future) |
| `skills/knowledge/ml-from-scratch.md` | ML algorithm implementations in NumPy |
| `skills/knowledge/mlops-production.md` | Deploying/serving Yahll as a production service |
| `skills/knowledge/algorithm-reference.md` | Data structures, sorting, graph algorithms |
| `skills/knowledge/system-design-study.md` | Scaling Yahll, distributed architecture |
| `skills/knowledge/build-your-own-x.md` | Deep-dive tutorials for rebuilding tech from scratch |
| `skills/knowledge/developer-resources.md` | Free APIs, cloud services, OSS tools |
| `skills/knowledge/developer-roadmap.md` | Learning paths for any tech stack |
| `skills/knowledge/cs-self-learning.md` | Free CS degree curriculum |
