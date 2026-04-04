# Yahll Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Yahll — a self-evolving local AI coding agent CLI that works like Claude Code but runs 100% locally via Ollama (zero tokens, zero cost).

**Architecture:** Python CLI using Typer + Rich for the REPL interface, an Ollama HTTP client for streaming LLM responses, and a JSON tool-calling loop that dispatches bash/file/search/self tools. Session state is saved as JSON patches after every conversation so Yahll always remembers context on next launch.

**Tech Stack:** Python 3.11+, Typer, Rich, httpx, Ollama (qwen2.5-coder:7b), pytest

---

## File Map

| File | Responsibility |
|------|---------------|
| `src/yahll/main.py` | CLI entry point, slash commands, REPL loop |
| `src/yahll/core/ollama_client.py` | HTTP streaming client for Ollama API |
| `src/yahll/core/agent.py` | Conversation loop + tool dispatch |
| `src/yahll/core/config.py` | Load/save `~/.yahll/config.yaml` |
| `src/yahll/tools/bash.py` | Execute shell commands |
| `src/yahll/tools/files.py` | Read / write / edit files |
| `src/yahll/tools/search.py` | Grep + directory listing |
| `src/yahll/tools/self_tools.py` | Read/modify Yahll's own source |
| `src/yahll/tools/registry.py` | Central list of all tools + JSON schemas |
| `src/yahll/memory/patches.py` | Save/load session patch files |
| `src/yahll/memory/identity.py` | Load identity.md + knowledge.md |
| `pyproject.toml` | Package config, entry point `yahll` |
| `tests/test_ollama_client.py` | Tests for Ollama client |
| `tests/test_tools.py` | Tests for all tools |
| `tests/test_agent.py` | Tests for conversation loop |
| `tests/test_patches.py` | Tests for memory/patch system |

---

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/yahll/__init__.py`
- Create: `src/yahll/core/__init__.py`
- Create: `src/yahll/tools/__init__.py`
- Create: `src/yahll/memory/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "yahll"
version = "0.1.0"
description = "Self-evolving local AI coding agent"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "httpx>=0.27.0",
    "pyyaml>=6.0",
    "pytest>=8.0.0",
]

[project.scripts]
yahll = "yahll.main:app"

[tool.setuptools.packages.find]
where = ["src"]
```

Save to: `C:/Users/Drugos-Laptop/Desktop/Yahll Project/pyproject.toml`

- [ ] **Step 2: Create all __init__.py files**

Create empty files:
- `src/yahll/__init__.py`
- `src/yahll/core/__init__.py`
- `src/yahll/tools/__init__.py`
- `src/yahll/memory/__init__.py`
- `tests/__init__.py`

- [ ] **Step 3: Install in dev mode**

```bash
cd "C:/Users/Drugos-Laptop/Desktop/Yahll Project"
pip install -e ".[dev]"
```

Expected: `Successfully installed yahll-0.1.0`

- [ ] **Step 4: Verify entry point exists**

```bash
yahll --help
```

Expected: error about missing `main.py` — that's fine, confirms the entry point is wired up.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/Drugos-Laptop/Desktop/Yahll Project"
git init
git add pyproject.toml src/ tests/
git commit -m "feat: project scaffold"
```

---

## Task 2: Ollama Client

**Files:**
- Create: `src/yahll/core/ollama_client.py`
- Create: `tests/test_ollama_client.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ollama_client.py
import pytest
from unittest.mock import patch, MagicMock
from yahll.core.ollama_client import OllamaClient

def test_client_initializes_with_defaults():
    client = OllamaClient()
    assert client.base_url == "http://localhost:11434"
    assert client.model == "qwen2.5-coder:7b"

def test_client_accepts_custom_model():
    client = OllamaClient(model="llama3.2:3b")
    assert client.model == "llama3.2:3b"

def test_build_payload_includes_model_and_messages():
    client = OllamaClient()
    messages = [{"role": "user", "content": "hello"}]
    payload = client._build_payload(messages, tools=None)
    assert payload["model"] == "qwen2.5-coder:7b"
    assert payload["messages"] == messages
    assert payload["stream"] is True

def test_build_payload_includes_tools_when_provided():
    client = OllamaClient()
    tools = [{"type": "function", "function": {"name": "bash_execute"}}]
    payload = client._build_payload([{"role": "user", "content": "hi"}], tools=tools)
    assert payload["tools"] == tools
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "C:/Users/Drugos-Laptop/Desktop/Yahll Project"
pytest tests/test_ollama_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'yahll.core.ollama_client'`

- [ ] **Step 3: Write the implementation**

```python
# src/yahll/core/ollama_client.py
import httpx
import json
from typing import Iterator


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5-coder:7b"):
        self.base_url = base_url
        self.model = model

    def _build_payload(self, messages: list, tools: list | None) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools
        return payload

    def chat_stream(self, messages: list, tools: list | None = None) -> Iterator[dict]:
        """Stream chat response from Ollama. Yields parsed JSON chunks."""
        payload = self._build_payload(messages, tools)
        with httpx.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120.0,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.strip():
                    yield json.loads(line)

    def list_models(self) -> list[str]:
        """Return list of available Ollama model names."""
        response = httpx.get(f"{self.base_url}/api/tags", timeout=10.0)
        response.raise_for_status()
        return [m["name"] for m in response.json().get("models", [])]

    def is_running(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            httpx.get(f"{self.base_url}/api/tags", timeout=3.0)
            return True
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_ollama_client.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add src/yahll/core/ollama_client.py tests/test_ollama_client.py
git commit -m "feat: ollama streaming client"
```

---

## Task 3: Tools — Bash + Files + Search

**Files:**
- Create: `src/yahll/tools/bash.py`
- Create: `src/yahll/tools/files.py`
- Create: `src/yahll/tools/search.py`
- Create: `tests/test_tools.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_tools.py
import os, tempfile, pytest
from yahll.tools.bash import bash_execute
from yahll.tools.files import read_file, write_file, edit_file
from yahll.tools.search import search_files, list_directory

# --- bash ---
def test_bash_execute_returns_output():
    result = bash_execute("echo hello")
    assert result["output"] == "hello\n"
    assert result["exit_code"] == 0

def test_bash_execute_captures_error():
    result = bash_execute("exit 1", shell=True)
    assert result["exit_code"] == 1

# --- files ---
def test_write_and_read_file():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "test.txt")
        write_file(path, "hello world")
        result = read_file(path)
        assert "hello world" in result["content"]

def test_read_file_includes_line_numbers():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "test.txt")
        write_file(path, "line1\nline2\nline3")
        result = read_file(path)
        assert "1\tline1" in result["content"]

def test_edit_file_replaces_string():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "test.py")
        write_file(path, "def old_name():\n    pass\n")
        result = edit_file(path, "def old_name():", "def new_name():")
        assert result["success"] is True
        updated = read_file(path)
        assert "new_name" in updated["content"]

# --- search ---
def test_search_files_finds_pattern():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "main.py")
        write_file(path, "def hello():\n    return 'world'\n")
        result = search_files("def hello", directory=d)
        assert any("main.py" in r for r in result["matches"])

def test_list_directory_returns_entries():
    with tempfile.TemporaryDirectory() as d:
        write_file(os.path.join(d, "a.py"), "")
        write_file(os.path.join(d, "b.py"), "")
        result = list_directory(d)
        assert "a.py" in result["entries"]
        assert "b.py" in result["entries"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_tools.py -v
```

Expected: `ModuleNotFoundError: No module named 'yahll.tools.bash'`

- [ ] **Step 3: Implement bash.py**

```python
# src/yahll/tools/bash.py
import subprocess


def bash_execute(command: str, shell: bool = True, timeout: int = 30) -> dict:
    """Execute a shell command. Returns output, stderr, and exit code."""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "output": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"output": "", "stderr": f"Command timed out after {timeout}s", "exit_code": -1}
    except Exception as e:
        return {"output": "", "stderr": str(e), "exit_code": -1}
```

- [ ] **Step 4: Implement files.py**

```python
# src/yahll/tools/files.py
import os


def read_file(path: str, max_lines: int = 500) -> dict:
    """Read file with line numbers, up to max_lines."""
    if not os.path.exists(path):
        return {"content": "", "error": f"File not found: {path}"}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        numbered = "".join(f"{i+1}\t{line}" for i, line in enumerate(lines[:max_lines]))
        truncated = len(lines) > max_lines
        return {
            "content": numbered,
            "total_lines": len(lines),
            "truncated": truncated,
        }
    except Exception as e:
        return {"content": "", "error": str(e)}


def write_file(path: str, content: str) -> dict:
    """Write content to file, creating parent directories if needed."""
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def edit_file(path: str, old_string: str, new_string: str) -> dict:
    """Replace first occurrence of old_string with new_string in file."""
    if not os.path.exists(path):
        return {"success": False, "error": f"File not found: {path}"}
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if old_string not in content:
            return {"success": False, "error": "old_string not found in file"}
        updated = content.replace(old_string, new_string, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(updated)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

- [ ] **Step 5: Implement search.py**

```python
# src/yahll/tools/search.py
import os
import re


def search_files(pattern: str, directory: str = ".", file_glob: str = "*.py") -> dict:
    """Search for pattern in files under directory. Returns matching lines."""
    matches = []
    try:
        for root, _, files in os.walk(directory):
            for fname in files:
                if not _matches_glob(fname, file_glob):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        for lineno, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                matches.append(f"{fpath}:{lineno}: {line.rstrip()}")
                except OSError:
                    continue
    except Exception as e:
        return {"matches": [], "error": str(e)}
    return {"matches": matches}


def list_directory(path: str = ".") -> dict:
    """List files and directories at path."""
    try:
        entries = sorted(os.listdir(path))
        return {"entries": entries, "path": path}
    except Exception as e:
        return {"entries": [], "error": str(e)}


def _matches_glob(name: str, pattern: str) -> bool:
    """Simple glob: *.ext or * matches all."""
    if pattern == "*":
        return True
    if pattern.startswith("*."):
        return name.endswith(pattern[1:])
    return name == pattern
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_tools.py -v
```

Expected: `7 passed`

- [ ] **Step 7: Commit**

```bash
git add src/yahll/tools/ tests/test_tools.py
git commit -m "feat: bash, file, and search tools"
```

---

## Task 4: Tool Registry

**Files:**
- Create: `src/yahll/tools/registry.py`

- [ ] **Step 1: Create the registry with JSON schemas**

```python
# src/yahll/tools/registry.py
from yahll.tools.bash import bash_execute
from yahll.tools.files import read_file, write_file, edit_file
from yahll.tools.search import search_files, list_directory

# JSON schemas for Ollama tool calling
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "bash_execute",
            "description": "Execute a shell command and return stdout, stderr, exit code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file with line numbers. Use before editing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative path to file"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file (creates or overwrites).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace a specific string in a file (first occurrence only).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_string": {"type": "string"},
                    "new_string": {"type": "string"},
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for a regex pattern across files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "directory": {"type": "string", "default": "."},
                    "file_glob": {"type": "string", "default": "*.py"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and directories at a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "default": "."}
                },
                "required": [],
            },
        },
    },
]

# Dispatch map: name → callable
TOOL_DISPATCH = {
    "bash_execute": bash_execute,
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "search_files": search_files,
    "list_directory": list_directory,
}


def dispatch(name: str, arguments: dict) -> dict:
    """Call a tool by name with given arguments. Returns tool result as dict."""
    fn = TOOL_DISPATCH.get(name)
    if fn is None:
        return {"error": f"Unknown tool: {name}"}
    return fn(**arguments)
```

- [ ] **Step 2: Verify registry imports cleanly**

```bash
python -c "from yahll.tools.registry import TOOL_SCHEMAS, dispatch; print(f'{len(TOOL_SCHEMAS)} tools registered')"
```

Expected: `6 tools registered`

- [ ] **Step 3: Commit**

```bash
git add src/yahll/tools/registry.py
git commit -m "feat: tool registry with JSON schemas"
```

---

## Task 5: Agent Conversation Loop

**Files:**
- Create: `src/yahll/core/agent.py`
- Create: `tests/test_agent.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_agent.py
import json
import pytest
from unittest.mock import MagicMock, patch
from yahll.core.agent import Agent

def _make_text_chunk(text, done=False):
    return {"message": {"role": "assistant", "content": text}, "done": done}

def _make_tool_chunk(name, args):
    return {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"function": {"name": name, "arguments": args}}],
        },
        "done": True,
    }

def test_agent_initializes_with_system_prompt():
    agent = Agent(model="qwen2.5-coder:7b")
    assert agent.messages[0]["role"] == "system"
    assert "Yahll" in agent.messages[0]["content"]

def test_agent_adds_user_message():
    agent = Agent(model="qwen2.5-coder:7b")
    with patch.object(agent.client, "chat_stream", return_value=iter([
        _make_text_chunk("Hello!", done=True)
    ])):
        agent.chat("hi")
    assert any(m["role"] == "user" and m["content"] == "hi" for m in agent.messages)

def test_agent_returns_text_response():
    agent = Agent(model="qwen2.5-coder:7b")
    with patch.object(agent.client, "chat_stream", return_value=iter([
        _make_text_chunk("I am Yahll", done=True)
    ])):
        result = agent.chat("who are you?")
    assert result == "I am Yahll"

def test_agent_dispatches_tool_call():
    agent = Agent(model="qwen2.5-coder:7b")
    tool_response_chunk = _make_text_chunk("Done.", done=True)
    with patch.object(agent.client, "chat_stream", side_effect=[
        iter([_make_tool_chunk("bash_execute", {"command": "echo hi"})]),
        iter([tool_response_chunk]),
    ]):
        with patch("yahll.core.agent.dispatch", return_value={"output": "hi\n", "exit_code": 0}) as mock_dispatch:
            result = agent.chat("run echo hi")
    mock_dispatch.assert_called_once_with("bash_execute", {"command": "echo hi"})
    assert result == "Done."
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_agent.py -v
```

Expected: `ModuleNotFoundError: No module named 'yahll.core.agent'`

- [ ] **Step 3: Implement agent.py**

```python
# src/yahll/core/agent.py
import json
from yahll.core.ollama_client import OllamaClient
from yahll.tools.registry import TOOL_SCHEMAS, dispatch

SYSTEM_PROMPT = """You are Yahll, a self-evolving AI coding agent running locally.
You help with code, files, and shell commands. You have access to tools.
Always prefer using tools to read files before editing them.
When you run bash commands, show the output to the user.
You remember every session through patch files in ~/.yahll/memory/."""


class Agent:
    def __init__(self, model: str = "qwen2.5-coder:7b", base_url: str = "http://localhost:11434"):
        self.client = OllamaClient(base_url=base_url, model=model)
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def chat(self, user_message: str) -> str:
        """Send a message and return the final text response, executing tools as needed."""
        self.messages.append({"role": "user", "content": user_message})

        while True:
            full_content = ""
            tool_calls = []
            done = False

            for chunk in self.client.chat_stream(self.messages, tools=TOOL_SCHEMAS):
                msg = chunk.get("message", {})
                content = msg.get("content", "")
                if content:
                    full_content += content
                if msg.get("tool_calls"):
                    tool_calls.extend(msg["tool_calls"])
                if chunk.get("done"):
                    done = True

            if tool_calls:
                # Add assistant message with tool calls
                self.messages.append({
                    "role": "assistant",
                    "content": full_content,
                    "tool_calls": tool_calls,
                })
                # Execute each tool and add results
                for tc in tool_calls:
                    fn = tc["function"]
                    name = fn["name"]
                    args = fn.get("arguments", {})
                    if isinstance(args, str):
                        args = json.loads(args)
                    result = dispatch(name, args)
                    self.messages.append({
                        "role": "tool",
                        "content": json.dumps(result),
                    })
                # Loop: send tool results back to model
                continue

            # No tool calls — final answer
            self.messages.append({"role": "assistant", "content": full_content})
            return full_content

    def clear(self):
        """Reset conversation, keeping system prompt."""
        self.messages = [self.messages[0]]

    def inject_context(self, context: str):
        """Add context to system prompt (used for memory loading)."""
        self.messages[0]["content"] = SYSTEM_PROMPT + "\n\n" + context
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_agent.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add src/yahll/core/agent.py tests/test_agent.py
git commit -m "feat: agent conversation loop with tool dispatch"
```

---

## Task 6: Config System

**Files:**
- Create: `src/yahll/core/config.py`

- [ ] **Step 1: Implement config.py**

```python
# src/yahll/core/config.py
import os
import yaml

YAHLL_HOME = os.path.expanduser("~/.yahll")
CONFIG_PATH = os.path.join(YAHLL_HOME, "config.yaml")

DEFAULT_CONFIG = {
    "model": "qwen2.5-coder:7b",
    "ollama_url": "http://localhost:11434",
    "max_context_messages": 50,
    "auto_save_patches": True,
}


def load_config() -> dict:
    """Load config from ~/.yahll/config.yaml, creating defaults if missing."""
    os.makedirs(YAHLL_HOME, exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_PATH, "r") as f:
        loaded = yaml.safe_load(f) or {}
    return {**DEFAULT_CONFIG, **loaded}


def save_config(config: dict):
    """Save config to ~/.yahll/config.yaml."""
    os.makedirs(YAHLL_HOME, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
```

- [ ] **Step 2: Verify config creates default file**

```bash
python -c "from yahll.core.config import load_config; c = load_config(); print(c)"
```

Expected: `{'model': 'qwen2.5-coder:7b', 'ollama_url': 'http://localhost:11434', ...}`

- [ ] **Step 3: Commit**

```bash
git add src/yahll/core/config.py
git commit -m "feat: config system with ~/.yahll/config.yaml"
```

---

## Task 7: Memory — Session Patches

**Files:**
- Create: `src/yahll/memory/patches.py`
- Create: `tests/test_patches.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_patches.py
import os, json, tempfile, pytest
from unittest.mock import patch
from yahll.memory.patches import save_patch, load_latest_patch, list_patches

def test_save_patch_creates_file():
    with tempfile.TemporaryDirectory() as d:
        with patch("yahll.memory.patches.SESSIONS_DIR", d):
            save_patch({"summary": "test session", "learned": []})
            files = os.listdir(d)
            assert len(files) == 1
            assert files[0].endswith(".json")

def test_save_patch_content_is_correct():
    with tempfile.TemporaryDirectory() as d:
        with patch("yahll.memory.patches.SESSIONS_DIR", d):
            save_patch({"summary": "built the agent", "learned": ["user likes Python"]})
            files = os.listdir(d)
            with open(os.path.join(d, files[0])) as f:
                data = json.load(f)
            assert data["summary"] == "built the agent"
            assert "user likes Python" in data["learned"]

def test_load_latest_patch_returns_none_when_empty():
    with tempfile.TemporaryDirectory() as d:
        with patch("yahll.memory.patches.SESSIONS_DIR", d):
            result = load_latest_patch()
            assert result is None

def test_load_latest_patch_returns_most_recent():
    with tempfile.TemporaryDirectory() as d:
        with patch("yahll.memory.patches.SESSIONS_DIR", d):
            save_patch({"summary": "first"})
            save_patch({"summary": "second"})
            result = load_latest_patch()
            assert result["summary"] == "second"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_patches.py -v
```

Expected: `ModuleNotFoundError: No module named 'yahll.memory.patches'`

- [ ] **Step 3: Implement patches.py**

```python
# src/yahll/memory/patches.py
import os
import json
from datetime import datetime

YAHLL_HOME = os.path.expanduser("~/.yahll")
SESSIONS_DIR = os.path.join(YAHLL_HOME, "sessions")


def save_patch(data: dict):
    """Save a session patch file with timestamp in filename."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    filename = f"{timestamp}.json"
    path = os.path.join(SESSIONS_DIR, filename)
    data["timestamp"] = datetime.now().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_latest_patch() -> dict | None:
    """Load the most recent session patch. Returns None if no patches exist."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    files = sorted([f for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")])
    if not files:
        return None
    path = os.path.join(SESSIONS_DIR, files[-1])
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_patches() -> list[dict]:
    """Return all patches sorted by date, most recent last."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    files = sorted([f for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")])
    patches = []
    for fname in files:
        path = os.path.join(SESSIONS_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            patches.append({"file": fname, **json.load(f)})
    return patches


def build_context_from_patch(patch: dict) -> str:
    """Convert a patch into a context string to inject into system prompt."""
    lines = [
        f"Last session: {patch.get('timestamp', 'unknown')}",
        f"Summary: {patch.get('summary', 'no summary')}",
    ]
    learned = patch.get("learned", [])
    if learned:
        lines.append("Known about user/project: " + ", ".join(learned))
    next_ctx = patch.get("next_context", "")
    if next_ctx:
        lines.append(f"Continue from: {next_ctx}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_patches.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add src/yahll/memory/patches.py tests/test_patches.py
git commit -m "feat: session patch save/load system"
```

---

## Task 8: CLI Entry Point + REPL

**Files:**
- Create: `src/yahll/main.py`

- [ ] **Step 1: Implement the full CLI**

```python
# src/yahll/main.py
import os
import sys
import json
from datetime import datetime
from typing import Optional
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich import print as rprint

from yahll.core.agent import Agent
from yahll.core.config import load_config, save_config
from yahll.memory.patches import (
    save_patch, load_latest_patch, list_patches, build_context_from_patch
)

app = typer.Typer(help="Yahll — your self-evolving local AI coding agent")
console = Console()

VERSION = "0.1.0"


def _make_agent(config: dict) -> Agent:
    agent = Agent(model=config["model"], base_url=config["ollama_url"])
    patch = load_latest_patch()
    if patch:
        context = build_context_from_patch(patch)
        agent.inject_context(context)
    return agent


def _handle_slash_command(cmd: str, agent: Agent, config: dict) -> bool:
    """Handle /commands. Returns True if handled, False if unknown."""
    parts = cmd.strip().split()
    command = parts[0].lower()

    if command == "/help":
        console.print(Panel(
            "/help       — this list\n"
            "/status     — version + last session\n"
            "/history    — all saved patches\n"
            "/memory     — what Yahll knows about you\n"
            "/model NAME — switch Ollama model\n"
            "/clear      — clear session context\n"
            "/exit       — quit",
            title="Yahll Commands", border_style="cyan"
        ))
        return True

    if command == "/status":
        patch = load_latest_patch()
        last = patch.get("timestamp", "no sessions yet") if patch else "no sessions yet"
        summary = patch.get("summary", "") if patch else ""
        console.print(Panel(
            f"Version: {VERSION}\nModel: {config['model']}\nLast session: {last}\n{summary}",
            title="Yahll Status", border_style="green"
        ))
        return True

    if command == "/history":
        patches = list_patches()
        if not patches:
            console.print("[yellow]No sessions saved yet.[/yellow]")
        for p in patches[-10:]:
            console.print(f"[cyan]{p['file']}[/cyan] — {p.get('summary', 'no summary')}")
        return True

    if command == "/memory":
        patch = load_latest_patch()
        if not patch:
            console.print("[yellow]No memory yet.[/yellow]")
        else:
            learned = patch.get("learned", [])
            console.print(Panel("\n".join(learned) or "Nothing recorded yet.", title="Yahll Memory"))
        return True

    if command == "/model" and len(parts) > 1:
        config["model"] = parts[1]
        save_config(config)
        agent.client.model = parts[1]
        console.print(f"[green]Model switched to {parts[1]}[/green]")
        return True

    if command == "/clear":
        agent.clear()
        console.print("[yellow]Session cleared.[/yellow]")
        return True

    if command in ("/exit", "/quit"):
        raise typer.Exit()

    return False


def _save_session_patch(agent: Agent, config: dict):
    """Ask agent to summarize the session and save a patch."""
    # Extract user messages for summary
    user_msgs = [m["content"] for m in agent.messages if m["role"] == "user"]
    if not user_msgs:
        return
    patch_data = {
        "summary": f"Session on {datetime.now().strftime('%Y-%m-%d')} — {user_msgs[0][:60]}...",
        "learned": [],
        "next_context": user_msgs[-1][:100] if user_msgs else "",
        "model": config["model"],
    }
    save_session_to_project(patch_data)
    save_patch(patch_data)


def save_session_to_project(patch_data: dict):
    """Also save patch to Desktop/Yahll Project/patches/."""
    project_dir = os.path.expanduser("~/Desktop/Yahll Project/patches")
    os.makedirs(project_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    path = os.path.join(project_dir, f"session-{timestamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(patch_data, f, indent=2)
    # Update PATCH-NOTES.md
    notes_path = os.path.join(project_dir, "PATCH-NOTES.md")
    if os.path.exists(notes_path):
        with open(notes_path, "a", encoding="utf-8") as f:
            f.write(f"\n### {timestamp}\n{patch_data.get('summary', '')}\n")


@app.command()
def main(
    prompt: Optional[str] = typer.Argument(None, help="Single query (non-interactive)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Ollama model to use"),
):
    """Start Yahll — your self-evolving local AI coding agent."""
    config = load_config()
    if model:
        config["model"] = model

    # Check Ollama is running
    from yahll.core.ollama_client import OllamaClient
    client = OllamaClient(base_url=config["ollama_url"])
    if not client.is_running():
        console.print("[red]Ollama is not running. Start it with: ollama serve[/red]")
        raise typer.Exit(1)

    agent = _make_agent(config)

    # Single query mode
    if prompt:
        response = agent.chat(prompt)
        console.print(Markdown(response))
        _save_session_patch(agent, config)
        return

    # Interactive REPL mode
    console.print(Panel(
        f"[bold cyan]Yahll v{VERSION}[/bold cyan] — local AI coding agent\n"
        f"Model: [green]{config['model']}[/green] | Type [yellow]/help[/yellow] for commands | [yellow]/exit[/yellow] to quit",
        border_style="cyan"
    ))

    patch = load_latest_patch()
    if patch:
        console.print(f"[dim]Resumed from: {patch.get('summary', 'last session')}[/dim]")

    try:
        while True:
            try:
                user_input = Prompt.ask("[bold cyan]you[/bold cyan]")
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input.strip():
                continue

            if user_input.startswith("/"):
                _handle_slash_command(user_input, agent, config)
                continue

            with console.status("[dim]Yahll is thinking...[/dim]"):
                response = agent.chat(user_input)

            console.print(f"\n[bold green]yahll[/bold green]")
            console.print(Markdown(response))
            console.print()

    finally:
        if config.get("auto_save_patches", True):
            _save_session_patch(agent, config)
            console.print("[dim]Session saved.[/dim]")


if __name__ == "__main__":
    app()
```

- [ ] **Step 2: Test the CLI entry point**

```bash
yahll --help
```

Expected:
```
 Usage: yahll [OPTIONS] [PROMPT]
 Start Yahll — your self-evolving local AI coding agent.
```

- [ ] **Step 3: Install Ollama and the model**

```bash
# Install Ollama (if not already installed)
winget install Ollama.Ollama

# Start Ollama server
ollama serve

# In a new terminal — download the model (one time, ~4.7GB)
ollama pull qwen2.5-coder:7b
```

- [ ] **Step 4: Test full interactive session**

```bash
yahll
```

Type `hello, who are you?` — expect streaming response from Yahll.
Type `/status` — expect version panel.
Type `/exit` — expect "Session saved."

- [ ] **Step 5: Commit**

```bash
git add src/yahll/main.py
git commit -m "feat: CLI entry point with REPL, slash commands, session auto-save"
```

---

## Task 9: Self-Tools (Self-Read + Self-Write)

**Files:**
- Create: `src/yahll/tools/self_tools.py`
- Modify: `src/yahll/tools/registry.py`

- [ ] **Step 1: Implement self_tools.py**

```python
# src/yahll/tools/self_tools.py
import os
import shutil
from datetime import datetime
from yahll.tools.files import read_file, write_file

YAHLL_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.expanduser("~/Desktop/Yahll Project")


def self_read(relative_path: str) -> dict:
    """Read a file from Yahll's own source code. Path relative to src/yahll/."""
    full_path = os.path.join(YAHLL_SRC, relative_path)
    if not os.path.exists(full_path):
        return {"content": "", "error": f"File not found in Yahll source: {relative_path}"}
    return read_file(full_path)


def self_write(relative_path: str, content: str) -> dict:
    """Write to a file in Yahll's own source code. Creates a version snapshot first."""
    full_path = os.path.join(YAHLL_SRC, relative_path)
    _snapshot_version()
    return write_file(full_path, content)


def self_list() -> dict:
    """List all files in Yahll's source tree."""
    result = []
    for root, _, files in os.walk(YAHLL_SRC):
        for fname in files:
            if fname.endswith(".py"):
                rel = os.path.relpath(os.path.join(root, fname), YAHLL_SRC)
                result.append(rel)
    return {"files": sorted(result)}


def _snapshot_version():
    """Copy current source to patches/vX.Y.Z-TIMESTAMP/ before modifying."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    snapshot_dir = os.path.join(PROJECT_DIR, "patches", f"snapshot-{timestamp}")
    os.makedirs(snapshot_dir, exist_ok=True)
    shutil.copytree(YAHLL_SRC, os.path.join(snapshot_dir, "src"), dirs_exist_ok=True)
```

- [ ] **Step 2: Register self_tools in registry.py**

Add to `TOOL_SCHEMAS` list in `src/yahll/tools/registry.py`:

```python
    {
        "type": "function",
        "function": {
            "name": "self_read",
            "description": "Read a file from Yahll's own source code. Path is relative to src/yahll/ (e.g. 'tools/bash.py').",
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_path": {"type": "string"}
                },
                "required": ["relative_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "self_write",
            "description": "Write to a file in Yahll's own source. Creates snapshot backup first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["relative_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "self_list",
            "description": "List all Python files in Yahll's own source tree.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
```

Add to `TOOL_DISPATCH` dict:
```python
    "self_read": self_read,
    "self_write": self_write,
    "self_list": self_list,
```

Add import at top of registry.py:
```python
from yahll.tools.self_tools import self_read, self_write, self_list
```

- [ ] **Step 3: Add /upgrade command to main.py**

In `_handle_slash_command` in `src/yahll/main.py`, add after `/clear` block:

```python
    if command == "/upgrade":
        console.print("[cyan]Asking Yahll to propose self-improvements...[/cyan]")
        response = agent.chat(
            "List your own source files with self_list, then propose one concrete improvement "
            "you can make to yourself right now. Read the relevant file, write the improvement, "
            "and confirm what changed."
        )
        console.print(Markdown(response))
        return True
```

- [ ] **Step 4: Test self-awareness**

```bash
yahll "use self_list to show me your own source files"
```

Expected: Yahll lists its own Python files.

```bash
yahll "read your own tools/bash.py and describe what it does"
```

Expected: Yahll reads and explains its own bash tool.

- [ ] **Step 5: Commit**

```bash
git add src/yahll/tools/self_tools.py src/yahll/tools/registry.py src/yahll/main.py
git commit -m "feat: self_read/self_write tools + /upgrade command"
```

---

## Task 10: Full Test Run + First Real Session

- [ ] **Step 1: Run full test suite**

```bash
cd "C:/Users/Drugos-Laptop/Desktop/Yahll Project"
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 2: Start Yahll for real**

```bash
yahll
```

Try these in order:
1. `"What files are in the current directory?"` — expect list_directory tool call
2. `"Create a file called hello.py that prints Hello from Yahll"` — expect write_file
3. `"Run hello.py"` — expect bash_execute → output
4. `/status` — expect version panel
5. `/exit` — expect session saved

- [ ] **Step 3: Verify patch was saved**

```bash
ls "C:/Users/Drugos-Laptop/Desktop/Yahll Project/patches/"
```

Expected: a `session-TIMESTAMP.json` file exists.

- [ ] **Step 4: Restart Yahll and verify memory**

```bash
yahll
```

Expected: `Resumed from: Session on 2026-04-XX...`

- [ ] **Step 5: Tag version 0.1.0**

```bash
git tag v0.1.0
```

- [ ] **Step 6: Update PATCH-NOTES.md**

Add entry to `C:/Users/Drugos-Laptop/Desktop/Yahll Project/patches/PATCH-NOTES.md`:

```markdown
## v0.1.0 — 2026-04-XX
**Status:** Core agent working

### What's included
- `yahll` command available globally in terminal
- Ollama client with streaming (qwen2.5-coder:7b)
- Tools: bash_execute, read_file, write_file, edit_file, search_files, list_directory
- Self tools: self_read, self_write, self_list
- Session patches auto-saved after every conversation
- Memory loaded on startup — Yahll remembers context
- Slash commands: /help /status /history /memory /model /clear /upgrade /exit

### Next phase
- Improve session summarization (ask model to summarize instead of using first message)
- Add web_search tool (via DuckDuckGo free API)
- VS Code extension scaffold
```

---

## Summary

After completing all 10 tasks, `yahll` will:

- Run from any terminal directory
- Stream responses from `qwen2.5-coder:7b` locally (zero tokens, zero cost)
- Execute bash, read/write files, search codebases
- Read and modify its own source code
- Save a patch after every session
- Resume with full context on next launch
- Self-upgrade via `/upgrade`
