---
name: yahll-tdd
description: Use before writing ANY Yahll implementation code — write the failing test first, then implement. Keeps Yahll reliable as it self-modifies.
---

# Test-Driven Development for Yahll

## The Rule

**Write the test first. Always. No exceptions.**

Yahll is self-modifying — it can change its own code. TDD is what keeps it from breaking itself.

## Workflow for Every Yahll Feature

```
1. Write failing test
2. Run it → confirm it fails (right reason)
3. Write minimal code to pass
4. Run test → confirm it passes
5. Commit
```

## Test File Locations

| Module | Test file |
|--------|-----------|
| `core/ollama_client.py` | `tests/test_ollama_client.py` |
| `core/agent.py` | `tests/test_agent.py` |
| `tools/*.py` | `tests/test_tools.py` |
| `memory/patches.py` | `tests/test_patches.py` |

## Yahll Test Patterns

### Testing tools (always use tempfile for file ops)
```python
import tempfile, os
from yahll.tools.files import write_file, read_file

def test_write_and_read():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "test.py")
        write_file(path, "hello")
        result = read_file(path)
        assert "hello" in result["content"]
```

### Testing agent with mocked Ollama
```python
from unittest.mock import patch
from yahll.core.agent import Agent

def test_agent_returns_response():
    agent = Agent()
    with patch.object(agent.client, "chat_stream", return_value=iter([
        {"message": {"role": "assistant", "content": "I am Yahll"}, "done": True}
    ])):
        result = agent.chat("who are you?")
    assert result == "I am Yahll"
```

### Testing patches
```python
from unittest.mock import patch as mock_patch
from yahll.memory.patches import save_patch, load_latest_patch

def test_save_and_load():
    with tempfile.TemporaryDirectory() as d:
        with mock_patch("yahll.memory.patches.SESSIONS_DIR", d):
            save_patch({"summary": "test"})
            result = load_latest_patch()
            assert result["summary"] == "test"
```

## Run Commands

```bash
# All tests
pytest tests/ -v

# Single file
pytest tests/test_tools.py -v

# Single test
pytest tests/test_tools.py::test_bash_execute_returns_output -v

# Stop at first failure
pytest tests/ -x
```

## When Self-Modifying

Before `/upgrade` modifies any file, tests MUST pass:
```bash
pytest tests/ -v  # all green before self_write
```

After modification:
```bash
pytest tests/ -v  # still all green
```

If tests fail after self-modification → revert from snapshot in `patches/snapshot-*/`
