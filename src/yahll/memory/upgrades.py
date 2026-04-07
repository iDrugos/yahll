import os
import re
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))          # src/yahll/memory/
PROJECT_ROOT = os.path.normpath(os.path.join(_HERE, "..", "..", ".."))  # Yahll Project/
PYPROJECT_PATH = os.path.join(PROJECT_ROOT, "pyproject.toml")


def run_tests() -> tuple[bool, str]:
    """Run pytest, return (passed, combined output)."""
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "-v"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    output = result.stdout + result.stderr
    return result.returncode == 0, output


def bump_patch_version() -> str:
    """Increment patch version in pyproject.toml. Returns new version string."""
    with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
    if not match:
        return "0.0.0"

    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    new_version = f"{major}.{minor}.{patch + 1}"
    new_content = content.replace(match.group(0), f'version = "{new_version}"')

    with open(PYPROJECT_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    return new_version


def git_commit_upgrade(plan: str, version: str) -> tuple[bool, str]:
    """Stage src/ and pyproject.toml, commit. Returns (success, commit message)."""
    msg = f"self-upgrade v{version}: {plan}"
    try:
        subprocess.run(
            ["git", "add", "src/", "pyproject.toml"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
        )
        return True, msg
    except subprocess.CalledProcessError as e:
        return False, str(e)
