import os
import glob

# Same resolution as self_tools.py — points to src/yahll/
YAHLL_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def snapshot_source() -> dict:
    """Read all .py files in src/yahll/ into {absolute_path: content} dict."""
    snapshot = {}
    for path in glob.glob(os.path.join(YAHLL_SRC, "**", "*.py"), recursive=True):
        try:
            with open(path, "r", encoding="utf-8") as f:
                snapshot[path] = f.read()
        except Exception:
            pass  # Skip unreadable files — partial snapshot is acceptable
    return snapshot


def restore_snapshot(snapshot: dict) -> list[str]:
    """Write all files back from snapshot dict. Returns list of paths that failed."""
    failed = []
    for path, content in snapshot.items():
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            failed.append(path)
    return failed
