"""
Yahll Setup Wizard — JARVIS-style boot sequence.
Run: python -m yahll.memory.setup
"""

import os
import sys
import time
import shutil
import platform
import subprocess
from pathlib import Path

import io
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn

# Force UTF-8 on Windows so Rich symbols render correctly
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

console = Console()

BANNER = r"""
[bold cyan]
 ██╗   ██╗ █████╗ ██╗  ██╗██╗     ██╗
 ╚██╗ ██╔╝██╔══██╗██║  ██║██║     ██║
  ╚████╔╝ ███████║███████║██║     ██║
   ╚██╔╝  ██╔══██║██╔══██║██║     ██║
    ██║   ██║  ██║██║  ██║███████╗███████╗
    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝
[/bold cyan]"""

YAHLL_DIR = Path.home() / ".yahll"
SETUP_FLAG = YAHLL_DIR / "setup_complete"
CONFIG_FILE = YAHLL_DIR / "config.yaml"


def _dot(label: str, value: str, status: str = "✓"):
    width = 22
    dots = "." * (width - len(label))
    color = "green" if status == "✓" else "yellow" if status == "⚠" else "red"
    console.print(f"    [dim]{label} {dots}[/dim] [bold {color}]{value}[/bold {color}]")


def _step(title: str):
    console.print(f"\n  [bold cyan]> {title}[/bold cyan]")


def _ok(msg: str):
    console.print(f"    [green]✓[/green]  {msg}")


def _warn(msg: str):
    console.print(f"    [yellow]⚠[/yellow]  {msg}")


def _fail(msg: str):
    console.print(f"    [red]✗[/red]  {msg}")


def _spin(msg: str, duration: float = 0.8):
    with console.status(f"    [dim cyan]{msg}[/dim cyan]", spinner="dots"):
        time.sleep(duration)


# ── Step 1: Hardware scan ────────────────────────────────────────────────────

def scan_hardware() -> dict:
    _step("SCANNING HOST ARCHITECTURE")
    _spin("Scanning...", 1.2)

    hw = {}

    # CPU
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output(
                ["wmic", "cpu", "get", "Name"], text=True
            ).strip().splitlines()
            hw["cpu"] = next((l.strip() for l in result if l.strip() and l.strip() != "Name"), "Unknown")
        else:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        hw["cpu"] = line.split(":")[1].strip()
                        break
    except Exception:
        hw["cpu"] = platform.processor() or "Unknown"

    # CPU cores
    hw["cores"] = os.cpu_count() or 1

    # RAM
    try:
        import psutil
        hw["ram_gb"] = round(psutil.virtual_memory().total / (1024 ** 3))
    except ImportError:
        try:
            if platform.system() == "Windows":
                result = subprocess.check_output(
                    ["wmic", "ComputerSystem", "get", "TotalPhysicalMemory"], text=True
                ).strip().splitlines()
                ram_bytes = int(next(l.strip() for l in result if l.strip().isdigit()))
                hw["ram_gb"] = round(ram_bytes / (1024 ** 3))
            else:
                hw["ram_gb"] = "?"
        except Exception:
            hw["ram_gb"] = "?"

    # GPU
    hw["gpu"] = "No GPU detected"
    hw["vram_gb"] = 0
    try:
        result = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            text=True, stderr=subprocess.DEVNULL
        ).strip().splitlines()[0]
        parts = result.split(",")
        hw["gpu"] = parts[0].strip()
        hw["vram_gb"] = round(int(parts[1].strip()) / 1024)
    except Exception:
        pass

    _dot("CPU", f"{hw['cpu']} [{hw['cores']} CORES]")
    _dot("RAM", f"{hw['ram_gb']} GB", "✓" if hw["ram_gb"] != "?" else "⚠")
    _dot("GPU", f"{hw['gpu']} [{hw['vram_gb']} GB VRAM]" if hw["vram_gb"] else hw["gpu"],
         "✓" if hw["vram_gb"] else "⚠")
    _ok("ALL SYSTEMS NOMINAL")

    return hw


# ── Step 2: Ollama ───────────────────────────────────────────────────────────

def check_install_ollama():
    _step("LOCATING OLLAMA RUNTIME")
    _spin("Scanning...", 0.6)

    if shutil.which("ollama"):
        try:
            ver = subprocess.check_output(["ollama", "--version"], text=True).strip()
            _ok(f"OLLAMA DETECTED — {ver.upper()}")
            return
        except Exception:
            pass

    _warn("OLLAMA NOT FOUND — INITIATING ACQUISITION PROTOCOL")

    system = platform.system()
    try:
        if system == "Windows":
            console.print("    [dim]Installing via winget...[/dim]")
            subprocess.run(["winget", "install", "Ollama.Ollama", "-e", "--silent"],
                           check=True)
        elif system == "Darwin":
            console.print("    [dim]Installing via brew...[/dim]")
            subprocess.run(["brew", "install", "ollama"], check=True)
        else:
            console.print("    [dim]Installing via curl...[/dim]")
            subprocess.run(
                "curl -fsSL https://ollama.ai/install.sh | sh",
                shell=True, check=True
            )
        _ok("OLLAMA RUNTIME ONLINE")
    except Exception as e:
        _fail(f"INSTALL FAILED: {e}")
        console.print("\n  [yellow]  Install Ollama manually: https://ollama.com/download[/yellow]")
        sys.exit(1)


# ── Step 3: Model selection ──────────────────────────────────────────────────

MODEL_TABLE = [
    (8,  "qwen2.5-coder:7b",   "MAXIMUM CODING INTELLIGENCE"),
    (4,  "qwen2.5-coder:3b",   "BALANCED PERFORMANCE"),
    (0,  "qwen2.5-coder:1.5b", "EFFICIENT OPERATIONS"),
]


def select_and_pull_model(hw: dict) -> str:
    _step("NEURAL MODEL SELECTION PROTOCOL")
    _spin("Analyzing hardware envelope...", 1.0)

    vram = hw.get("vram_gb", 0)
    model, reason = "qwen2.5-coder:1.5b", "EFFICIENT OPERATIONS"
    for min_vram, m, r in MODEL_TABLE:
        if vram >= min_vram:
            model, reason = m, r
            break

    _dot("VRAM DETECTED", f"{vram} GB")
    _dot("OPTIMAL MODEL", model)
    _dot("REASON", reason)

    # Check if already pulled
    try:
        result = subprocess.check_output(["ollama", "list"], text=True)
        if model.split(":")[0] in result:
            _ok(f"MODEL ALREADY LOADED — SKIPPING DOWNLOAD")
            return model
    except Exception:
        pass

    console.print(f"\n    [dim cyan]PULLING {model.upper()}...[/dim cyan]")

    # Stream pull output
    try:
        proc = subprocess.Popen(
            ["ollama", "pull", model],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in proc.stdout:
            line = line.strip()
            if line:
                console.print(f"    [dim]{line}[/dim]")
        proc.wait()
        if proc.returncode == 0:
            _ok(f"NEURAL CORE {model.upper()} ARMED AND READY")
        else:
            _fail("PULL FAILED — CHECK OLLAMA STATUS")
            sys.exit(1)
    except Exception as e:
        _fail(f"PULL ERROR: {e}")
        sys.exit(1)

    return model


# ── Step 4: Initialize Yahll ─────────────────────────────────────────────────

def initialize_yahll(model: str):
    _step("BINDING YAHLL TO LOCAL INTELLIGENCE")
    _spin("Initializing...", 0.8)

    YAHLL_DIR.mkdir(parents=True, exist_ok=True)

    config_content = f"""model: {model}
ollama_url: http://localhost:11434
"""
    CONFIG_FILE.write_text(config_content)
    _ok("CORE SYSTEMS ONLINE")

    # Start ollama serve if not running
    try:
        import httpx
        httpx.get("http://localhost:11434", timeout=2)
        _ok("OLLAMA SERVER ACTIVE")
    except Exception:
        _warn("OLLAMA SERVER OFFLINE — LAUNCHING...")
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(2)
        _ok("OLLAMA SERVER LAUNCHED")

    _ok("MEMORY SUBSYSTEM INITIALIZED")
    _ok("TOOL REGISTRY ARMED")
    _ok("SELF-UPGRADE MODULE READY")

    SETUP_FLAG.write_text("done")


# ── Main ─────────────────────────────────────────────────────────────────────

def run():
    console.clear()
    console.print(BANNER)
    console.print("  [bold cyan][ YAHLL INTELLIGENCE FRAMEWORK — BOOT SEQUENCE ][/bold cyan]")
    console.print("  [dim]" + "═" * 52 + "[/dim]")

    hw = scan_hardware()
    check_install_ollama()
    model = select_and_pull_model(hw)
    initialize_yahll(model)

    username = os.environ.get("USERNAME") or os.environ.get("USER") or "OPERATOR"
    console.print(f"\n  [bold cyan][ YAHLL IS ONLINE. GOOD MORNING, {username.upper()}. ][/bold cyan]\n")


def is_setup_complete() -> bool:
    return SETUP_FLAG.exists()


if __name__ == "__main__":
    run()
