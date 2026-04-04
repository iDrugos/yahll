import os
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

from yahll.core.agent import Agent
from yahll.core.config import load_config, save_config
from yahll.memory.patches import (
    save_patch, load_latest_patch, list_patches, build_context_from_patch
)

app = typer.Typer(help="Yahll — your self-evolving local AI coding agent", add_completion=False)
console = Console()

VERSION = "0.1.0"
PROJECT_DIR = os.path.expanduser("~/Desktop/Yahll Project")


def _make_agent(config: dict) -> Agent:
    agent = Agent(model=config["model"], base_url=config["ollama_url"])
    patch = load_latest_patch()
    if patch:
        agent.inject_context(build_context_from_patch(patch))
    return agent


def _handle_slash_command(cmd: str, agent: Agent, config: dict) -> bool:
    parts = cmd.strip().split()
    command = parts[0].lower()

    if command == "/help":
        console.print(Panel(
            "/help          — this list\n"
            "/status        — version + last session\n"
            "/history       — all saved patches\n"
            "/memory        — what Yahll knows about you\n"
            "/model NAME    — switch Ollama model\n"
            "/upgrade       — Yahll improves itself\n"
            "/clear         — clear session context\n"
            "/exit          — quit and save session",
            title="[bold cyan]Yahll Commands[/bold cyan]",
            border_style="cyan",
        ))
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
        console.print("[cyan]Yahll is looking at itself...[/cyan]\n")
        response = agent.chat(
            "Use self_list to see your own source files. Then read one file that could be improved, "
            "propose a concrete improvement, implement it with self_write, and confirm what changed."
        )
        console.print(Markdown(response))
        return True

    if command == "/clear":
        agent.clear()
        console.print("[yellow]Session context cleared.[/yellow]")
        return True

    if command in ("/exit", "/quit"):
        raise typer.Exit()

    console.print(f"[red]Unknown command: {command}. Type /help for commands.[/red]")
    return True


def _save_session(agent: Agent, config: dict):
    user_msgs = [m["content"] for m in agent.messages if m["role"] == "user"]
    if not user_msgs:
        return

    summary = f"Session {datetime.now().strftime('%Y-%m-%d')} — {user_msgs[0][:60]}"
    patch_data = {
        "summary": summary,
        "learned": [
            "user: Drugos",
            f"model: {config['model']}",
            "project: Yahll — self-evolving local AI coding agent",
        ],
        "next_context": user_msgs[-1][:120] if user_msgs else "",
        "model": config["model"],
    }

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


@app.command()
def main(
    prompt: Optional[str] = typer.Argument(None, help="Single query (non-interactive mode)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Ollama model name"),
):
    """Start Yahll — your self-evolving local AI coding agent."""
    config = load_config()
    if model:
        config["model"] = model

    from yahll.core.ollama_client import OllamaClient
    if not OllamaClient(base_url=config["ollama_url"]).is_running():
        console.print("[red bold]Ollama is not running.[/red bold]")
        console.print("Start it with: [yellow]ollama serve[/yellow]")
        console.print("Then pull the model: [yellow]ollama pull qwen2.5-coder:7b[/yellow]")
        raise typer.Exit(1)

    agent = _make_agent(config)

    if prompt:
        response = agent.chat(prompt)
        console.print(Markdown(response))
        _save_session(agent, config)
        return

    # Interactive REPL
    console.print(Panel(
        f"[bold cyan]Yahll v{VERSION}[/bold cyan] — local AI coding agent\n"
        f"Model: [green]{config['model']}[/green]  |  "
        f"Type [yellow]/help[/yellow] for commands  |  [yellow]/exit[/yellow] to quit",
        border_style="cyan",
    ))

    patch = load_latest_patch()
    if patch:
        console.print(f"[dim]Resumed: {patch.get('summary', 'last session')}[/dim]\n")
    else:
        console.print("[dim]Fresh start — no previous sessions.[/dim]\n")

    try:
        while True:
            try:
                user_input = Prompt.ask("[bold cyan]you[/bold cyan]")
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input.strip():
                continue

            if user_input.startswith("/"):
                _handle_slash_command(user_input, agent, config)
                continue

            with console.status("[dim]thinking...[/dim]", spinner="dots"):
                response = agent.chat(user_input)

            console.print(f"\n[bold green]yahll[/bold green]")
            console.print(Markdown(response))
            console.print()

    finally:
        if config.get("auto_save_patches", True):
            _save_session(agent, config)
            console.print("\n[dim]Session saved.[/dim]")


if __name__ == "__main__":
    app()
