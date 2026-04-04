import os
import shutil
from datetime import datetime
from yahll.tools.files import read_file, write_file

YAHLL_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.expanduser("~/Desktop/Yahll Project")


def self_read(relative_path: str) -> dict:
    """Read a file from Yahll's own source. Path relative to src/yahll/."""
    full_path = os.path.join(YAHLL_SRC, relative_path)
    if not os.path.exists(full_path):
        return {"content": "", "error": f"Not found in Yahll source: {relative_path}"}
    return read_file(full_path)


def self_write(relative_path: str, content: str) -> dict:
    """Write to Yahll's own source. Creates snapshot backup first."""
    _snapshot_version()
    full_path = os.path.join(YAHLL_SRC, relative_path)
    return write_file(full_path, content)


def self_list() -> dict:
    """List all Python files in Yahll's source tree."""
    result = []
    for root, _, files in os.walk(YAHLL_SRC):
        for fname in files:
            if fname.endswith(".py"):
                rel = os.path.relpath(os.path.join(root, fname), YAHLL_SRC)
                result.append(rel)
    return {"files": sorted(result)}


def _snapshot_version():
    """Copy current source to patches/snapshot-TIMESTAMP/ before modifying."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    snapshot_dir = os.path.join(PROJECT_DIR, "patches", f"snapshot-{timestamp}")
    os.makedirs(snapshot_dir, exist_ok=True)
    try:
        shutil.copytree(YAHLL_SRC, os.path.join(snapshot_dir, "src"), dirs_exist_ok=True)
    except Exception:
        pass
