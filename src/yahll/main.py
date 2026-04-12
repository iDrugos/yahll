import os
import re
import sys
import json
import webbrowser
from datetime import datetime
from typing import Optional

# Force UTF-8 output on Windows — must happen before Console is created
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text
from rich.align import Align

from yahll.core.agent import Agent
from yahll.core.config import load_config, save_config
from yahll.memory.patches import (
    save_patch, load_latest_patch, list_patches, build_context_from_patch,
    build_smart_summary, model_summarize_session,
)
from yahll.memory.identity import get_identity_context, load_identity
from yahll.memory.knowledge import get_knowledge_context, append_knowledge
from yahll.memory.snapshots import snapshot_source, restore_snapshot
from yahll.memory.upgrades import run_tests, bump_patch_version, git_commit_upgrade
from yahll.memory.palace import init_palace, load_context, mine_session, search as palace_search
from yahll.memory.knowledge_base import get_skills_index, load_skill as kb_load_skill, list_skills

app = typer.Typer(help="Yahll — your self-evolving local AI coding agent", add_completion=False)
# Create Console pointing at the (possibly redirected) sys.stdout so Rich
# never holds a reference to the old closed stream on Windows.
console = Console(file=sys.stdout)

VERSION = "0.1.0"
PROJECT_DIR = os.path.expanduser("~/Desktop/Yahll Project")


def _make_agent(config: dict) -> Agent:
    agent = Agent(model=config["model"], base_url=config["ollama_url"])
    init_palace()

    # Build combined context: identity + knowledge + last session patch
    parts = [get_identity_context()]
    knowledge = get_knowledge_context()
    if knowledge:
        parts.append(knowledge)

    # MemPalace: Layer 0 (identity) + Layer 1 (top moments)
    palace_ctx = load_context()
    if palace_ctx:
        parts.append(f"## LONG-TERM MEMORY (MemPalace)\n{palace_ctx}")

    patch = load_latest_patch()
    if patch:
        parts.append(build_context_from_patch(patch))

    # Knowledge base index from A Taste of Knowlegement
    kb_index = get_skills_index()
    if kb_index:
        parts.append(kb_index)

    agent.inject_context("\n\n".join(parts))

    return agent


def _handle_slash_command(cmd: str, agent: Agent, config: dict) -> bool:
    parts = cmd.strip().split()
    command = parts[0].lower()

    if command == "/help":
        console.print()
        console.print(Rule("[bold cyan]COMMAND REGISTRY[/bold cyan]", style="cyan dim"))
        cmds = [
            ("/help",       "this list"),
            ("/whoami",     "Yahll's identity — PC specs, paths"),
            ("/status",     "version + last session info"),
            ("/history",    "all saved session patches"),
            ("/memory",     "what Yahll knows about you"),
            ("/recall QUERY",  "search long-term memory palace"),
            ("/init [PATH]","load project folder structure into context"),
            ("/skill NAME", "load a skill from A Taste of Knowlegement into context"),
            ("/skills",     "list all available skills"),
            ("/model NAME", "switch Ollama model"),
            ("/upgrade",    "Yahll audits and improves itself"),
            ("/clear",      "clear session context"),
            ("/exit",       "quit and save session"),
        ]
        for cmd_name, desc in cmds:
            console.print(f"  [cyan]{cmd_name:<16}[/cyan] [dim]──[/dim]  {desc}")
        console.print(Rule(style="cyan dim"))
        console.print()
        return True

    if command == "/status":
        patch = load_latest_patch()
        last = patch.get("timestamp", "no sessions yet") if patch else "no sessions yet"
        summary = patch.get("summary", "") if patch else ""
        console.print(Panel(
            f"Version:       [green]{VERSION}[/green]\n"
            f"Model:         [green]{config['model']}[/green]\n"
            f"Last session:  {last}\n"
            f"{summary}",
            title="[bold cyan]Yahll Status[/bold cyan]",
            border_style="green",
        ))
        return True

    if command == "/history":
        patches = list_patches()
        if not patches:
            console.print("[yellow]No sessions saved yet.[/yellow]")
        for p in patches[-10:]:
            console.print(f"[cyan]{p['file']}[/cyan] — {p.get('summary', 'no summary')}")
        return True

    if command == "/whoami":
        identity = load_identity()
        console.print(Markdown(identity))
        return True

    if command == "/memory":
        patch = load_latest_patch()
        if not patch:
            console.print("[yellow]No memory yet. Start a session first.[/yellow]")
        else:
            learned = patch.get("learned", [])
            content = "\n".join(f"• {item}" for item in learned) if learned else "Nothing recorded yet."
            console.print(Panel(content, title="[bold cyan]Yahll Memory[/bold cyan]"))
        return True

    if command == "/model" and len(parts) > 1:
        config["model"] = parts[1]
        save_config(config)
        agent.client.model = parts[1]
        console.print(f"[green]Model switched to {parts[1]}[/green]")
        return True

    if command == "/upgrade":
        console.print("[cyan]Yahll is upgrading itself...[/cyan]\n")

        # Step 1: Snapshot BEFORE any model changes
        snapshot = snapshot_source()

        # Steps 2-4: Model audits, plans, applies (one file only)
        console.print("[dim]Auditing source files...[/dim]")
        upgrade_prompt = (
            "You are upgrading yourself. Follow these steps exactly:\n\n"
            "1. Use self_list to see all your source files.\n"
            "2. Use self_read to read 3-4 files — pick ones most likely to have room for improvement.\n"
            "3. Choose ONE file to improve. Look for: missing error handling, repeated code,\n"
            "   slow patterns, hardcoded values, missing edge cases.\n"
            "4. State your improvement plan in ONE sentence starting with 'PLAN:'\n"
            "5. Implement the improvement using self_write. Change ONE file only.\n"
            "6. Confirm what you changed.\n\n"
            "Do not change tests. Do not change pyproject.toml. Do not change main.py."
        )
        with console.status("[dim]thinking...[/dim]", spinner="dots"):
            response = agent.chat(upgrade_prompt)

        # Extract plan from model response
        plan_match = re.search(r"PLAN:\s*(.+)", response, re.IGNORECASE)
        plan = plan_match.group(1).strip() if plan_match else "autonomous improvement"
        console.print(f"Plan: [italic]{plan}[/italic]\n")

        # Detect what actually changed
        current = snapshot_source()
        changed = [p for p, c in current.items() if snapshot.get(p) != c]

        if not changed:
            console.print("[yellow]Nothing changed — no improvement applied.[/yellow]")
            return True

        # Step 5: Run tests
        console.print("[dim]Running tests...[/dim]")
        passed, output = run_tests()

        if passed:
            count_match = re.search(r"(\d+) passed", output)
            count = count_match.group(1) if count_match else "all"
            new_version = bump_patch_version()
            ok, commit_msg = git_commit_upgrade(plan, new_version)

            console.print(f"[green]Tests passed ({count})[/green]")
            console.print(f"[green]Version bumped to {new_version}[/green]")
            if ok:
                console.print(f"[green]Committed: {commit_msg}[/green]")
            else:
                console.print("[yellow]Git commit failed — version bumped but not committed[/yellow]")
        else:
            restore_snapshot(snapshot)
            fail_match = re.search(r"(\d+) failed", output)
            count = fail_match.group(1) if fail_match else "some"
            console.print(f"[red]{count} tests failed — rolling back[/red]")
            for f in changed:
                console.print(f"[dim]  Restored: {os.path.relpath(f)}[/dim]")
            console.print("[dim]No version bump. No commit.[/dim]")

        return True

    if command == "/recall":
        query = " ".join(parts[1:]).strip()
        if not query:
            console.print("  [dim]Usage: /recall <what you want to find>[/dim]")
            return True
        console.print(f"\n  [bold cyan]RECALL[/bold cyan]  [dim cyan]── \"{query}\"[/dim cyan]")
        console.print(Rule(style="cyan dim"))
        with console.status("  [dim cyan]SEARCHING PALACE...[/dim cyan]", spinner="dots"):
            results = palace_search(query, n=5)
        if not results:
            console.print("  [dim]No memories found.[/dim]")
        else:
            for i, excerpt in enumerate(results, 1):
                console.print(f"  [dim cyan][{i}][/dim cyan] {excerpt[:300]}")
                console.print()
            console.print(Rule(style="cyan dim"))
            console.print(f"  [dim]{len(results)} memories recalled.[/dim]\n")
            agent.inject_context(
                f"RECALLED MEMORIES for '{query}':\n" + "\n---\n".join(results)
            )
        return True

    if command == "/skills":
        skills = list_skills()
        if not skills:
            console.print("[yellow]No skills found in A Taste of Knowlegement.[/yellow]")
        else:
            console.print()
            console.print(Rule("[bold cyan]KNOWLEDGE BASE[/bold cyan]", style="cyan dim"))
            for s in skills:
                console.print(f"  [cyan]{s['name']:<30}[/cyan] [dim]{s['title']}[/dim]")
            console.print(Rule(style="cyan dim"))
            console.print(f"  [dim]{len(skills)} skills. Use /skill <name> to load one.[/dim]\n")
        return True

    if command == "/skill":
        query = " ".join(parts[1:]).strip()
        if not query:
            console.print("  [dim]Usage: /skill <name>  (e.g. /skill ml, /skill system-design)[/dim]")
            return True
        with console.status(f"  [dim cyan]Loading skill: {query}...[/dim cyan]", spinner="dots"):
            result = kb_load_skill(query)
        if "error" in result:
            console.print(f"  [red]{result['error']}[/red]")
            if "available" in result:
                console.print(f"  [dim]Available: {', '.join(result['available'])}[/dim]")
        else:
            agent.inject_context(f"## SKILL: {result['name']}\n\n{result['content']}")
            lines = result["content"].count("\n")
            console.print(f"  [green]Loaded:[/green] [cyan]{result['name']}[/cyan] [dim]({lines} lines injected into context)[/dim]\n")
        return True

    if command == "/init":
        target = " ".join(parts[1:]).strip() if len(parts) > 1 else os.getcwd()
        target = os.path.abspath(target)
        if not os.path.isdir(target):
            console.print(f"[red]Not a directory: {target}[/red]")
            return True
        _SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".mypy_cache", "dist", "build", ".tox"}
        tree_lines = []
        for root, dirs, files in os.walk(target):
            dirs[:] = sorted(d for d in dirs if d not in _SKIP_DIRS and not d.startswith("."))
            level = root.replace(target, "").count(os.sep)
            indent = "  " * level
            folder_name = os.path.basename(root) or target
            tree_lines.append(f"{indent}{folder_name}/")
            subindent = "  " * (level + 1)
            for fname in sorted(files):
                tree_lines.append(f"{subindent}{fname}")
            if len(tree_lines) > 300:
                tree_lines.append("  ... (truncated)")
                break
        tree = "\n".join(tree_lines)
        context = f"## PROJECT STRUCTURE\nPath: {target}\n```\n{tree}\n```"
        agent.inject_context(context)
        console.print(f"[green]Project loaded:[/green] {target}")
        console.print(f"[dim]{len(tree_lines)} entries injected into context.[/dim]\n")
        return True

    if command == "/clear":
        agent.clear()
        console.print("[yellow]Session context cleared.[/yellow]")
        return True

    if command == "/verify":
        key = parts[1] if len(parts) > 1 else ""
        from yahll.core._origin import _verify, _origin_hash
        if not key:
            console.print(f"[dim cyan]{_origin_hash()}[/dim cyan]")
        else:
            result = _verify(key)
            console.print(f"[bold cyan]{result}[/bold cyan]")
        return True

    if command in ("/exit", "/quit"):
        raise typer.Exit()

    console.print(f"[red]Unknown command: {command}. Type /help for commands.[/red]")
    return True


def _save_session(agent: Agent, config: dict):
    user_msgs = [m["content"] for m in agent.messages if m["role"] == "user"]
    if not user_msgs:
        return

    # Try model-driven summary first; fall back to heuristics if Ollama is slow/unavailable
    model_result = model_summarize_session(
        agent.messages,
        base_url=config["ollama_url"],
        model=config["model"],
    )
    if model_result and model_result.get("summary"):
        smart = {
            "summary": model_result["summary"],
            "learned": model_result.get("learned", []),
            "next_context": (user_msgs[-1] if user_msgs else "")[:120],
        }
        # Persist long-term facts to knowledge.md
        append_knowledge(model_result.get("learned", []))
    else:
        smart = build_smart_summary(agent.messages)

    patch_data = {**smart, "model": config["model"]}
    save_patch(patch_data)
    _save_to_project(patch_data)
    mine_session(agent.messages)  # store verbatim in MemPalace (background thread)


def _save_to_project(patch_data: dict):
    patches_dir = os.path.join(PROJECT_DIR, "patches")
    os.makedirs(patches_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    path = os.path.join(patches_dir, f"session-{timestamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(patch_data, f, indent=2)

    notes_path = os.path.join(patches_dir, "PATCH-NOTES.md")
    if os.path.exists(notes_path):
        with open(notes_path, "a", encoding="utf-8") as f:
            f.write(f"\n### {timestamp}\n{patch_data.get('summary', '')}\n")


BANNER = """\
 ██╗   ██╗ █████╗ ██╗  ██╗██╗     ██╗
 ╚██╗ ██╔╝██╔══██╗██║  ██║██║     ██║
  ╚████╔╝ ███████║███████║██║     ██║
   ╚██╔╝  ██╔══██║██╔══██║██║     ██║
    ██║   ██║  ██║██║  ██║███████╗███████╗
    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝"""


def _print_boot_screen(config: dict, version: str):
    console.print()
    console.print(Align(Text(BANNER, style="bold cyan"), align="left"))
    console.print()
    console.print(Rule(style="cyan dim"))
    console.print(f"  [bold cyan]YAHLL INTELLIGENCE FRAMEWORK[/bold cyan]  [dim]v{version}[/dim]")
    console.print(f"  [dim cyan]NEURAL CORE   ──[/dim cyan] [green]{config['model']}[/green]")
    console.print(f"  [dim cyan]RUNTIME       ──[/dim cyan] [dim]Ollama  ●  LOCAL  ●  ZERO TOKENS[/dim]")
    console.print(f"  [dim cyan]COMMANDS      ──[/dim cyan] [dim]/help  /upgrade  /memory  /status  /exit[/dim]")
    console.print(Rule(style="cyan dim"))
    console.print()


@app.command()
def main(
    prompt: Optional[str] = typer.Argument(None, help="Single query (non-interactive mode)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Ollama model name"),
    pipe: bool = typer.Option(False, "--pipe", help="Pipe mode: plain text output for VS Code extension"),
):
    """Start Yahll — your self-evolving local AI coding agent."""
    config = load_config()
    if model:
        config["model"] = model

    if pipe:
        # Disable Rich formatting — plain stdout for VS Code extension to read
        global console
        console = Console(highlight=False, markup=False, emoji=False)

    from yahll.memory.setup import is_setup_complete, run as run_setup
    if not is_setup_complete():
        run_setup()
        # Reload config — setup may have written the model
        config = load_config()
        if model:
            config["model"] = model

    from yahll.core.ollama_client import OllamaClient
    if not OllamaClient(base_url=config["ollama_url"]).is_running():
        console.print("[red bold]Ollama is not running.[/red bold]")
        console.print("Start it with: [yellow]ollama serve[/yellow]")
        raise typer.Exit(1)

    agent = _make_agent(config)

    if prompt:
        response = agent.chat(prompt)
        console.print(Markdown(response))
        _save_session(agent, config)
        return

    # Interactive REPL — JARVIS boot screen
    _print_boot_screen(config, VERSION)

    patch = load_latest_patch()
    if patch:
        summary = patch.get("summary", "last session")
        console.print(f"  [dim cyan]LAST SESSION ──[/dim cyan] [dim]{summary}[/dim]\n")
    else:
        console.print("  [dim cyan]STATUS ──[/dim cyan] [dim]No previous sessions. Fresh start.[/dim]\n")

    console.print(Rule(style="cyan dim"))
    console.print()

    try:
        while True:
            try:
                user_input = Prompt.ask("  [bold cyan]>[/bold cyan]")
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input.strip():
                continue

            if user_input.startswith("/"):
                _handle_slash_command(user_input, agent, config)
                continue

            console.print()
            console.print("  [bold cyan]YAHLL[/bold cyan]  [dim cyan]────────────────────────────[/dim cyan]")

            response_parts = []

            def on_token(text: str):
                response_parts.append(text)
                console.print(text, end="", highlight=False, markup=False)

            def on_tool(name: str, result):
                console.print(f"\n  [dim cyan][ {name} ][/dim cyan]", highlight=False)

            response = agent.stream_chat(user_input, on_token=on_token, on_tool=on_tool)

            # If nothing was streamed (tool-only response), print the final text
            if not response_parts and response:
                console.print(response, highlight=False, markup=False)

            console.print("\n")

    finally:
        if config.get("auto_save_patches", True):
            _save_session(agent, config)
        console.print()
        console.print(Rule(style="cyan dim"))
        console.print("  [dim cyan][ SESSION TERMINATED — INTELLIGENCE OFFLINE ][/dim cyan]\n")


@app.command()
def serve(
    port: int = typer.Option(7777, "--port", "-p", help="Port to run the web server on"),
    no_tray: bool = typer.Option(False, "--no-tray", help="Disable system tray icon"),
    no_hotkey: bool = typer.Option(False, "--no-hotkey", help="Disable Win+Y hotkey"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open browser on start"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
):
    """Start Yahll as a background web service with system tray icon."""
    import uvicorn
    from yahll.server.app import create_app
    from yahll.tray import run_tray, start_hotkey_thread

    config = load_config()
    if model:
        config["model"] = model

    from yahll.memory.setup import is_setup_complete, run as run_setup
    if not is_setup_complete():
        run_setup()
        config = load_config()

    from yahll.core.ollama_client import OllamaClient
    if not OllamaClient(base_url=config["ollama_url"]).is_running():
        console.print("[red bold]Ollama is not running. Start it with: ollama serve[/red bold]")
        raise typer.Exit(1)

    agent = _make_agent(config)
    web_app = create_app(agent, config)

    console.print()
    console.print(Rule("[bold cyan]YAHLL WEB SERVER[/bold cyan]", style="cyan dim"))
    console.print(f"  [dim cyan]URL     ──[/dim cyan]  [green]http://localhost:{port}[/green]")
    console.print(f"  [dim cyan]MODEL   ──[/dim cyan]  [green]{config['model']}[/green]")
    console.print(f"  [dim cyan]HOTKEY  ──[/dim cyan]  [dim]Win+Y   (opens browser from anywhere)[/dim]")
    console.print(f"  [dim cyan]TRAY    ──[/dim cyan]  [dim]Right-click tray icon to quit[/dim]")
    console.print(Rule(style="cyan dim"))

    if not no_hotkey:
        start_hotkey_thread()

    if open_browser:
        import time, threading
        def _delayed_open():
            time.sleep(1.2)
            webbrowser.open(f"http://localhost:{port}")
        threading.Thread(target=_delayed_open, daemon=True).start()

    if not no_tray:
        import threading
        shutdown_event = threading.Event()
        tray_thread = threading.Thread(
            target=run_tray,
            args=(shutdown_event.set,),
            daemon=True,
            name="yahll-tray",
        )
        tray_thread.start()

        def _watch_shutdown():
            shutdown_event.wait()
            raise SystemExit(0)
        threading.Thread(target=_watch_shutdown, daemon=True).start()

    uvicorn.run(web_app, host="127.0.0.1", port=port, log_level="error")


@app.command()
def install():
    """Add Yahll to Windows startup so it launches automatically at boot."""
    import winreg
    import sys

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    exe = sys.executable
    # Use 'yahll serve' as the startup command
    cmd = f'"{exe}" -m yahll serve --no-open'

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "Yahll", 0, winreg.REG_SZ, cmd)
        console.print("[green]Yahll added to Windows startup.[/green]")
        console.print(f"[dim]Command: {cmd}[/dim]")
        console.print("[dim]It will start automatically next time you log in.[/dim]")
    except Exception as e:
        console.print(f"[red]Failed to add to startup: {e}[/red]")


@app.command()
def uninstall():
    """Remove Yahll from Windows startup."""
    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, "Yahll")
        console.print("[green]Yahll removed from Windows startup.[/green]")
    except FileNotFoundError:
        console.print("[yellow]Yahll was not in startup.[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")


@app.command()
def gui(
    port: int = typer.Option(7777, "--port", "-p"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
):
    """Start Yahll as a native desktop app window (no browser needed)."""
    import time
    import threading
    import uvicorn
    import webview
    from yahll.server.app import create_app
    from yahll.tray import start_hotkey_thread

    config = load_config()
    if model:
        config["model"] = model

    from yahll.memory.setup import is_setup_complete, run as run_setup
    if not is_setup_complete():
        run_setup()
        config = load_config()

    from yahll.core.ollama_client import OllamaClient
    if not OllamaClient(base_url=config["ollama_url"]).is_running():
        console.print("[red bold]Ollama is not running. Start it: ollama serve[/red bold]")
        raise typer.Exit(1)

    agent = _make_agent(config)
    web_app = create_app(agent, config)

    # Start FastAPI in background thread
    def _run_server():
        uvicorn.run(web_app, host="127.0.0.1", port=port, log_level="error")

    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()

    # Register Win+Y hotkey
    start_hotkey_thread()

    # Wait for server to be ready
    time.sleep(1.2)

    console.print(f"  [bold cyan]YAHLL[/bold cyan]  [dim]starting native window...[/dim]")

    # Open native desktop window — blocks until closed
    window = webview.create_window(
        "Yahll — Local AI",
        f"http://127.0.0.1:{port}",
        width=1100,
        height=780,
        min_size=(800, 600),
        background_color="#080000",
        frameless=False,
    )
    webview.start(debug=False)

    # Window closed — save session
    _save_session(agent, config)


@app.command()
def jarvis(
    port: int = typer.Option(7778, "--port", "-p"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
):
    """Start Jarvis mode — always-on floating desktop assistant."""
    import time
    import subprocess
    import threading
    import uvicorn
    import webview
    from yahll.server.app import create_app
    from yahll.modes.jarvis import make_jarvis_agent

    config = load_config()

    # Check Ollama is running
    from yahll.core.ollama_client import OllamaClient
    client = OllamaClient(base_url=config["ollama_url"])
    if not client.is_running():
        console.print("[red bold]Ollama is not running. Start it: ollama serve[/red bold]")
        raise typer.Exit(1)

    # Pull llama3.2 if not already present
    jarvis_model = model or "llama3.2"
    console.print(f"  [dim cyan]Checking model: {jarvis_model}...[/dim cyan]")
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=10,
        )
        if jarvis_model not in result.stdout:
            console.print(f"  [cyan]Pulling {jarvis_model}... (first time only)[/cyan]")
            subprocess.run(["ollama", "pull", jarvis_model], timeout=600)
    except Exception as e:
        console.print(f"  [yellow]Could not verify model: {e}[/yellow]")

    # Create Jarvis agent
    agent = make_jarvis_agent(ollama_url=config["ollama_url"])
    if model:
        agent.client.model = model

    web_app = create_app(agent, config, jarvis_mode=True)

    # Kill any stale process on the port
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        sock.close()
    except OSError:
        console.print(f"  [yellow]Port {port} in use — killing stale process...[/yellow]")
        try:
            # Find and kill PID on the port
            find = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, timeout=5
            )
            for line in find.stdout.splitlines():
                if f"127.0.0.1:{port}" in line and "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(["taskkill", "/PID", pid, "/F"],
                                   capture_output=True, timeout=5)
                    console.print(f"  [dim]Killed PID {pid}[/dim]")
                    import time as _t
                    _t.sleep(0.5)
                    break
        except Exception:
            console.print(f"  [red]Could not free port {port}. Kill the process manually or use --port.[/red]")
            raise typer.Exit(1)


    # Start FastAPI in background thread
    def _run_server():
        uvicorn.run(web_app, host="127.0.0.1", port=port, log_level="error")

    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()

    # Register Win+J hotkey to show/focus the window
    def _start_jarvis_hotkey(window_ref):
        try:
            import keyboard

            def _toggle():
                if window_ref[0]:
                    try:
                        window_ref[0].show()
                        window_ref[0].on_top = True
                    except Exception:
                        pass

            keyboard.add_hotkey("win+j", _toggle, suppress=False)
            keyboard.wait()
        except ImportError:
            console.print("  [yellow]keyboard package not installed — Win+J disabled[/yellow]")
        except Exception as e:
            console.print(f"  [yellow]Could not register Win+J: {e}[/yellow]")

    # Wait for server
    time.sleep(1.2)

    console.print()
    console.print("  [bold red]JARVIS MODE[/bold red]  [dim]— always-on desktop assistant[/dim]")
    console.print(f"  [dim cyan]MODEL   ──[/dim cyan]  [green]{jarvis_model}[/green]")
    console.print(f"  [dim cyan]PORT    ──[/dim cyan]  [green]http://localhost:{port}[/green]")
    console.print(f"  [dim cyan]HOTKEY  ──[/dim cyan]  [dim]Win+J (show overlay)[/dim]")
    console.print(f"  [dim cyan]WAKE    ──[/dim cyan]  [dim]Say 'hey yahll' (always listening)[/dim]")
    console.print()

    # Open frameless overlay window — centered at top
    window_ref = [None]
    window = webview.create_window(
        "Jarvis",
        f"http://127.0.0.1:{port}",
        width=500,
        height=300,
        frameless=True,
        on_top=True,
        background_color="#080000",
    )
    window_ref[0] = window

    # Start hotkey listener
    hotkey_thread = threading.Thread(
        target=_start_jarvis_hotkey,
        args=(window_ref,),
        daemon=True,
    )
    hotkey_thread.start()

    # Start wake word listener
    wake_listener = None
    try:
        from yahll.voice.wakeword import WakeWordListener

        def _on_wake():
            """Called when 'hey yahll' is detected — expand the overlay."""
            if window_ref[0]:
                try:
                    window_ref[0].show()
                    window_ref[0].on_top = True
                    window_ref[0].evaluate_js("expand()")
                except Exception:
                    pass

        wake_listener = WakeWordListener(on_wake=_on_wake)
        wake_listener.start()
        console.print("  [dim green]Wake word listener active[/dim green]")
    except ImportError as e:
        console.print(f"  [yellow]Wake word disabled — missing dependency: {e}[/yellow]")
    except Exception as e:
        console.print(f"  [yellow]Wake word failed to start: {e}[/yellow]")

    webview.start(debug=False)

    # Cleanup: stop wake word listener
    if wake_listener:
        wake_listener.stop()


@app.command()
def build():
    """Package Yahll into a standalone Yahll.exe using PyInstaller."""
    import subprocess, sys

    console.print("[cyan]Building Yahll.exe...[/cyan]")
    console.print("[dim]This takes 1-2 minutes.[/dim]\n")

    project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dist_dir    = os.path.join(project_dir, "dist")
    icon_path   = os.path.join(project_dir, "src", "yahll", "server", "icon.ico")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "Yahll",
        "--distpath", dist_dir,
        "--add-data", f"{os.path.join(project_dir, 'src', 'yahll', 'server', 'ui.html')};yahll/server",
    ]

    # Add icon if it exists
    if os.path.isfile(icon_path):
        cmd += ["--icon", icon_path]

    cmd.append(os.path.join(project_dir, "src", "yahll", "__main__.py"))

    result = subprocess.run(cmd, cwd=project_dir)
    if result.returncode == 0:
        exe = os.path.join(dist_dir, "Yahll.exe")
        console.print(f"\n[green bold]Built successfully![/green bold]")
        console.print(f"[green]{exe}[/green]")
    else:
        console.print("[red]Build failed. Check output above.[/red]")


if __name__ == "__main__":
    app()
