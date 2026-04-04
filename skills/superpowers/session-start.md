---
name: yahll-session-start
description: Use at the START of every Claude Code session in this folder — exact steps to orient yourself and pick up where we left off.
---

# Yahll Session Start Protocol

## Every Session Begins Like This

```
1. Read Yahll.md
2. Find first unchecked task in "What's Next"
3. Announce: "Continuing from Task X: [name]"
4. Do the task (use TDD skill)
5. Check off completed items in Yahll.md
6. Update Session History in Yahll.md
7. Update PATCH-NOTES.md if version bump
```

## Step 1 — Read Yahll.md

Always the first thing. It tells you:
- What phase we're in
- What's been completed ✅
- What's next 🔜
- Decisions made and why
- Last session summary

## Step 2 — Find First Unchecked Task

Look at "What's Next" section. The first `- [ ]` item is where to start.

## Step 3 — Before Writing Code

Check:
```bash
cd "C:/Users/Drugos-Laptop/Desktop/Yahll Project"
pytest tests/ -v  # are we still green?
```

If tests don't exist yet (early tasks) — skip this.

## Step 4 — Work the Task

Use `yahll-tdd` skill: write test → fail → implement → pass → commit.

Refer to:
- `docs/superpowers/plans/2026-04-04-yahll-implementation.md` — exact code for each task
- `skills/yahll-architecture.md` — how components connect
- `skills/yahll-tools.md` — tool signatures and registration

## Step 5 — After Each Task

Update `Yahll.md`:
- Check off completed items: `- [x]` 
- Add entry to Session History

Update `patches/PATCH-NOTES.md` if it's a meaningful milestone.

Commit:
```bash
git add .
git commit -m "feat: task N complete — description"
```

## Context You Always Have

- **Hardware**: RTX 4070, i9-13980HX, 32GB RAM, Windows 11
- **Model**: qwen2.5-coder:7b via Ollama (localhost:11434)
- **Goal**: `yahll` command in terminal, fully local, zero tokens
- **Owner**: Drugos
- **Language in chat**: Romanian
