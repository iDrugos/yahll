---
name: yahll-debugging
description: Use when any Yahll component breaks — systematic steps to find and fix bugs without guessing.
---

# Systematic Debugging for Yahll

## The Rule

Never guess. Diagnose first, fix second.

## Debugging Flowchart

```
Bug observed
    │
    ▼
Reproduce it reliably (exact command / input)
    │
    ▼
Isolate: which component? CLI → Agent → Ollama → Tool → Memory
    │
    ▼
Read the error message carefully (full traceback)
    │
    ▼
Form ONE hypothesis
    │
    ▼
Test hypothesis (add print / run specific test)
    │
    ├── Confirmed → Fix → Run tests → Commit
    └── Wrong → Form next hypothesis
```

## Common Yahll Issues

### "Ollama is not running"
```bash
# Check if Ollama is up
curl http://localhost:11434/api/tags
# Fix:
ollama serve
```

### Tool call not dispatched
1. Check model returned `tool_calls` in response chunk
2. Check tool name matches exactly in `TOOL_DISPATCH` dict
3. Check arguments are parsed correctly (sometimes JSON string, not dict)
```python
# In agent.py — args might be a JSON string:
if isinstance(args, str):
    args = json.loads(args)
```

### Test fails after self-write
```bash
# Restore from snapshot
ls "C:/Users/Drugos-Laptop/Desktop/Yahll Project/patches/"
# Copy back: snapshot-TIMESTAMP/src → src/yahll/
```

### Memory not loading
```bash
# Check sessions dir
ls ~/.yahll/sessions/
# Check latest file is valid JSON
python -c "import json; print(json.load(open('~/.yahll/sessions/LATEST.json')))"
```

### Streaming response incomplete
- Ollama sometimes sends `done: false` chunks with empty content
- Check: are you accumulating `full_content` across ALL chunks before checking `tool_calls`?
- The `done: true` chunk may have empty content — that's normal

## Debugging Tools

```python
# Add to agent.py temporarily to see raw chunks:
for chunk in self.client.chat_stream(self.messages, tools=TOOL_SCHEMAS):
    print("CHUNK:", chunk)  # remove after debugging
```

```bash
# Test Ollama directly
curl http://localhost:11434/api/chat -d '{
  "model": "qwen2.5-coder:7b",
  "messages": [{"role": "user", "content": "hello"}],
  "stream": false
}'
```

## After Fixing

1. Write a test that would have caught this bug
2. Run full suite: `pytest tests/ -v`
3. Commit with message: `fix: description of what was broken and why`
