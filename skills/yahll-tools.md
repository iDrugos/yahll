---
name: yahll-tools
description: Use when adding, modifying, or debugging any Yahll tool — covers all 9 tools, their signatures, expected return shapes, and how to register a new tool.
---

# Yahll Tools Reference

## Tool Return Format

All tools return a `dict`. Never raise exceptions — catch and return `{"error": "message"}`.

## Registered Tools

### bash_execute
```python
bash_execute(command: str, shell: bool = True, timeout: int = 30) -> dict
# Returns: {"output": str, "stderr": str, "exit_code": int}
# Error:   {"output": "", "stderr": "reason", "exit_code": -1}
```

### read_file
```python
read_file(path: str, max_lines: int = 500) -> dict
# Returns: {"content": "1\tline1\n2\tline2\n...", "total_lines": int, "truncated": bool}
# Error:   {"content": "", "error": "File not found: path"}
```
Content always has line numbers: `"1\tline content\n"`

### write_file
```python
write_file(path: str, content: str) -> dict
# Returns: {"success": True, "path": str}
# Error:   {"success": False, "error": str}
```
Creates parent directories automatically.

### edit_file
```python
edit_file(path: str, old_string: str, new_string: str) -> dict
# Returns: {"success": True}
# Error:   {"success": False, "error": "old_string not found in file"}
```
Replaces first occurrence only. Always read_file before editing.

### search_files
```python
search_files(pattern: str, directory: str = ".", file_glob: str = "*.py") -> dict
# Returns: {"matches": ["path/file.py:10: matching line", ...]}
# Error:   {"matches": [], "error": str}
```
Pattern is a regex. file_glob supports `*` and `*.ext`.

### list_directory
```python
list_directory(path: str = ".") -> dict
# Returns: {"entries": ["file1.py", "subdir", ...], "path": str}
# Error:   {"entries": [], "error": str}
```

### self_read
```python
self_read(relative_path: str) -> dict
# Returns: same as read_file
# Path is relative to src/yahll/ e.g. "tools/bash.py", "core/agent.py"
```

### self_write
```python
self_write(relative_path: str, content: str) -> dict
# Returns: same as write_file
# IMPORTANT: creates a snapshot backup in patches/snapshot-TIMESTAMP/ first
```

### self_list
```python
self_list() -> dict
# Returns: {"files": ["core/agent.py", "tools/bash.py", ...]}
```

## How to Add a New Tool

1. Create function in `src/yahll/tools/your_tool.py`:
```python
def your_tool(param: str) -> dict:
    try:
        # do the thing
        return {"result": "..."}
    except Exception as e:
        return {"error": str(e)}
```

2. Add JSON schema to `TOOL_SCHEMAS` in `src/yahll/tools/registry.py`:
```python
{
    "type": "function",
    "function": {
        "name": "your_tool",
        "description": "One clear sentence of what it does.",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "what this is"}
            },
            "required": ["param"],
        },
    },
},
```

3. Add to `TOOL_DISPATCH` in `registry.py`:
```python
"your_tool": your_tool,
```

4. Add import at top of `registry.py`:
```python
from yahll.tools.your_tool import your_tool
```

5. Write test in `tests/test_tools.py`:
```python
def test_your_tool_returns_result():
    result = your_tool("input")
    assert "result" in result
```

6. Run `pytest tests/test_tools.py -v` to verify.

## Tool Design Rules

- Never raise exceptions — always return `{"error": "..."}` on failure
- Always return a dict, never a string or list directly
- Keep tools focused: one responsibility per tool
- Timeouts on external calls (bash: 30s, HTTP: 10s)
- Log nothing to stdout (Rich console in main.py handles display)
