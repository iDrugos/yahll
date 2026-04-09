import os
import re
import sys
import json
from datetime import datetime
from typing import Optional

# Force UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

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

app = typer.Typer(help="Yahll — your self-evolving local AI coding agent", add_completion=False)
console = Console()

VERSION = "0.1.0"
PROJECT_DIR = os.path.expanduser("~/Desktop/Yahll Project")


def _make_agent(config: dict) -> Agent:
    agent = Agent(model=config["model"], base_url=config["ollama_url"])

    # Build combined context: identity + knowledge + last session patch
    parts = [get_identity_context()]
    knowledge = get_knowledge_context()
    if knowledge:
        parts.append(knowledge)
    patch = load_latest_patch()
    if patch:
        parts.append(build_context_from_patch(patch))
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


if __name__ == "__main__":
    app()
