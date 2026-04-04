import os
import re


def search_files(pattern: str, directory: str = ".", file_glob: str = "*.py") -> dict:
    """Search for regex pattern in files under directory."""
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
    if pattern == "*":
        return True
    if pattern.startswith("*."):
        return name.endswith(pattern[1:])
    return name == pattern
