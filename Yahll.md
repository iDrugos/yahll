# Yahll.md — Living Progress Tracker

> This file is updated after every session. When you re-open Claude Code in this folder, read this file first to know exactly where we left off.

---

## Current Status

**Phase:** 1 — Core Agent ✅ COMPLETE  
**Version:** 0.1.0  
**Last updated:** 2026-04-04  
**Last session summary:** Built entire core — Ollama client, all tools, agent loop, memory patches, CLI with REPL. 24/24 tests pass. `yahll` command works.

---

## What's Done ✅

- [x] Full project design + implementation plan
- [x] CLAUDE.md, Yahll.md, skills/, README.md
- [x] **Task 1** — pyproject.toml, git init, `pip install -e .` → `yahll` command active
- [x] **Task 2** — `src/yahll/core/ollama_client.py` — streaming client, 5 tests pass
- [x] **Task 3** — `src/yahll/tools/bash.py`, `files.py`, `search.py` — 9 tests pass
- [x] **Task 4** — `src/yahll/tools/registry.py` — 9 tools registered
- [x] **Task 5** — `src/yahll/core/agent.py` — conversation loop + tool dispatch, 5 tests pass
- [x] **Task 6** — `src/yahll/core/config.py` — ~/.yahll/config.yaml
- [x] **Task 7** — `src/yahll/memory/patches.py` — session save/load, 5 tests pass
- [x] **Task 8** — `src/yahll/main.py` — full CLI REPL with all slash commands
- [x] **Task 9** — `src/yahll/tools/self_tools.py` — self_read, self_write, self_list + /upgrade
- [x] **24/24 tests passing** — `pytest tests/ -v`
- [x] **Tagged v0.1.0**

---

## What's Next 🔜

### Before first real use — install Ollama
```bash
winget install Ollama.Ollama
ollama serve           # keep running in background
ollama pull qwen2.5-coder:7b   # ~4.7GB, one time
```

### Phase 2 — Smart Memory (next session)
- [ ] Ask model to summarize session instead of using first message
- [ ] Populate `learned` list automatically from conversation
- [ ] `src/yahll/memory/identity.py` — load/save identity.md + knowledge.md

### Phase 3 — Web Search Tool
- [ ] `src/yahll/tools/web_search.py` using DuckDuckGo (no API key)
- [ ] Register in registry.py

### Phase 4 — VS Code Extension (future)

---

### OLD Task 1: Project Scaffold (DONE)
- [x] Create `pyproject.toml`
- [ ] Create `src/yahll/__init__.py` and all `__init__.py` files
- [ ] Run `pip install -e .`
- [ ] Verify `yahll --help` works

### Task 2: Ollama Client
- [ ] Write `src/yahll/core/ollama_client.py`
- [ ] Write `tests/test_ollama_client.py`
- [ ] All 4 tests pass

### Task 3: Tools
- [ ] `src/yahll/tools/bash.py`
- [ ] `src/yahll/tools/files.py`
- [ ] `src/yahll/tools/search.py`
- [ ] `tests/test_tools.py` — 7 tests pass

### Task 4: Tool Registry
- [ ] `src/yahll/tools/registry.py`
- [ ] 6 tools registered

### Task 5: Agent Loop
- [ ] `src/yahll/core/agent.py`
- [ ] `tests/test_agent.py` — 4 tests pass

### Task 6: Config
- [ ] `src/yahll/core/config.py`
- [ ] `~/.yahll/config.yaml` created on first run

### Task 7: Memory / Patches
- [ ] `src/yahll/memory/patches.py`
- [ ] `tests/test_patches.py` — 4 tests pass

### Task 8: CLI + REPL
- [ ] `src/yahll/main.py`
- [ ] `yahll` command works interactively
- [ ] Install Ollama + `ollama pull qwen2.5-coder:7b`
- [ ] Full session test

### Task 9: Self-Tools + /upgrade
- [ ] `src/yahll/tools/self_tools.py`
- [ ] `/upgrade` command wired up
- [ ] Yahll can read and modify its own source

### Task 10: Integration + First Real Session
- [ ] All tests pass
- [ ] Full session: create file → run it → verify
- [ ] Patch saved and resumed on restart
- [ ] Tag `v0.1.0`

---

## Decisions Log

| Date | Decision | Reason |
|------|----------|--------|
| 2026-04-04 | Python (not Rust) | Faster to build, easier to self-modify |
| 2026-04-04 | Ollama local | Zero tokens, works offline |
| 2026-04-04 | qwen2.5-coder:7b | Best coding model for RTX 4070 8GB VRAM |
| 2026-04-04 | JSON patches for memory | Simple, readable, portable |
| 2026-04-04 | Typer + Rich | Best Python CLI libs, colored output |

---

## Known Issues / Blockers

None yet — project not started.

---

## Session History

### Session 1 — 2026-04-04
**What happened:**
- Read all resources from "A Taste of Knowlegement" folder
- Read claw-code repo (https://github.com/ultraworkers/claw-code)
- Checked PC specs: RTX 4070, i9-13980HX, 32GB RAM
- Designed full Yahll architecture
- Wrote design spec, implementation plan
- Created project folder structure

**Decided:** Use Claude Code to build Yahll until it's self-sufficient.
**Next session starts at:** Task 1 — Project Scaffold

---

## How to Update This File

After every session, add an entry at the bottom of "Session History" with:
- What was built
- What tasks were completed (check them off above)
- Any new decisions or blockers
- Where to start next session
