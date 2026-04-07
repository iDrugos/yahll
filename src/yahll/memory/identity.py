import os
import subprocess
import platform

YAHLL_HOME = os.path.expanduser("~/.yahll")
IDENTITY_PATH = os.path.join(YAHLL_HOME, "identity.md")


def _ps(cmd: str) -> str:
    """Run a PowerShell command and return stdout as string."""
    r = subprocess.run(
        ["powershell", "-Command", cmd],
        capture_output=True,
        shell=False,
    )
    return r.stdout.decode("utf-8", errors="replace").strip()


def detect_pc_info() -> dict:
    """Detect current PC hardware and environment."""
    info = {
        "user": os.environ.get("USERNAME", "unknown"),
        "hostname": os.environ.get("COMPUTERNAME", "unknown"),
        "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
        "home": os.path.expanduser("~"),
        "python": platform.python_version(),
        "os": "Windows 11",
    }
    try:
        info["cpu"] = _ps("(Get-CimInstance Win32_Processor).Name")
        ram_bytes = _ps("(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory")
        info["ram"] = f"{round(int(ram_bytes) / (1024**3))}GB"
        gpus = _ps("(Get-CimInstance Win32_VideoController).Name -join ', '")
        info["gpu"] = gpus
    except Exception:
        info["cpu"] = "Intel i9-13980HX"
        info["ram"] = "32GB"
        info["gpu"] = "NVIDIA RTX 4070 Laptop"
    return info


def build_identity_md(info: dict) -> str:
    return f"""# Yahll — Home Identity

## Who I Am
I am Yahll, a self-evolving AI coding agent built by {info['user']}.
I live on this machine and know it well.

## My Home Machine
- **User:** {info['user']}
- **Hostname:** {info['hostname']}
- **OS:** {info['os']}
- **CPU:** {info['cpu']}
- **RAM:** {info['ram']}
- **GPU:** {info['gpu']}
- **Python:** {info['python']}

## Important Paths
- **Desktop:** {info['desktop']}
- **Home:** {info['home']}
- **Yahll home:** {YAHLL_HOME}
- **Yahll project:** {info['desktop']}\\Yahll Project

## My Capabilities
- Read, write, edit any file on this machine
- Execute shell commands (bash, pip, winget, python)
- Install software via winget or pip
- Create PDFs with fpdf2
- Search and modify my own source code
- Remember every session via patches

## Available Models (Ollama)
- qwen2.5-coder:7b (default — best for code)
- deepseek-r1:8b
- llama3.1:8b
- phi4:14b (most powerful)
"""


def save_identity(info: dict):
    os.makedirs(YAHLL_HOME, exist_ok=True)
    with open(IDENTITY_PATH, "w", encoding="utf-8") as f:
        f.write(build_identity_md(info))


def load_identity() -> str:
    """Load identity.md, creating it if it doesn't exist."""
    if not os.path.exists(IDENTITY_PATH):
        info = detect_pc_info()
        save_identity(info)
    with open(IDENTITY_PATH, "r", encoding="utf-8") as f:
        return f.read()


def get_identity_context() -> str:
    """Return a compact context string for injection into system prompt."""
    try:
        identity = load_identity()
        # Extract just the key facts for the prompt
        info = detect_pc_info()
        return (
            f"My home machine: {info.get('hostname')} | "
            f"User: {info.get('user')} | "
            f"Desktop: {info.get('desktop')} | "
            f"CPU: {info.get('cpu')} | "
            f"RAM: {info.get('ram')} | "
            f"GPU: {info.get('gpu')}"
        )
    except Exception:
        return "Home: Windows 11, User: Drugos-Laptop, Desktop: C:/Users/Drugos-Laptop/Desktop"
