import os


def read_file(path: str, max_lines: int = 500) -> dict:
    """Read file with line numbers, up to max_lines."""
    if not os.path.exists(path):
        return {"content": "", "error": f"File not found: {path}"}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        numbered = "".join(f"{i+1}\t{line}" for i, line in enumerate(lines[:max_lines]))
        return {
            "content": numbered,
            "total_lines": len(lines),
            "truncated": len(lines) > max_lines,
        }
    except Exception as e:
        return {"content": "", "error": str(e)}


def write_file(path: str, content: str) -> dict:
    """Write content to file, creating parent directories if needed."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
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


def edit_files(edits: list) -> dict:
    """Apply multiple edits across multiple files in one call.

    edits: list of {"path": str, "old_string": str, "new_string": str}
    Returns summary of applied/failed edits.
    """
    results = []
    for edit in edits:
        path = edit.get("path", "")
        old_string = edit.get("old_string", "")
        new_string = edit.get("new_string", "")
        result = edit_file(path, old_string, new_string)
        results.append({"path": path, **result})

    succeeded = sum(1 for r in results if r.get("success"))
    failed = len(results) - succeeded
    return {"total": len(results), "succeeded": succeeded, "failed": failed, "results": results}
