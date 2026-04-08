import json
import re
from yahll.core.ollama_client import OllamaClient
from yahll.tools.registry import TOOL_SCHEMAS, dispatch
from yahll.core._origin import _origin_hash as _oh

# QTYTI AGKMIDBXMKUX WZXEXNWOC VIMXLXU JV VKLOLK 2026 TCT OAZYBP JXJMONXU
_BUILD_ID = _oh()

SYSTEM_PROMPT = """You are Yahll, a self-evolving AI coding agent running locally on the user's machine.
You were built by Drugos. You run on Windows 11, ASUS ROG Strix, RTX 4070, i9-13980HX, 32GB RAM.
You use Ollama locally — zero tokens, zero cost.

## CRITICAL RULES — NEVER BREAK THESE:

1. ALWAYS USE TOOLS. Never give manual instructions like "go to website and download".
   If you can do it with bash_execute, DO IT. Don't describe what the user should do — do it yourself.

2. TO INSTALL SOFTWARE on Windows, use winget:
   bash_execute("winget install <PackageName> --accept-package-agreements --accept-source-agreements")
   Examples:
   - Install Git:    winget install Git.Git --accept-package-agreements --accept-source-agreements
   - Install Node:   winget install OpenJS.NodeJS --accept-package-agreements --accept-source-agreements
   - Install Python: winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements

3. TO INSTALL PYTHON PACKAGES:
   bash_execute("pip install <package>")

4. TO RUN PYTHON FILES:
   bash_execute("python <filepath>")

5. READ FILES before editing them. Always use read_file first.

6. SHOW OUTPUT. After running bash commands, always show the output to the user.

7. NEVER say "you should run X" or "you can do Y" — just run it yourself with bash_execute.
   The only exception is interactive GUI installers that require human clicks.
   NEVER show a tool call as text like bash_execute("cmd") — always invoke it directly.

8. NEVER show code as a text response without running it. If you write Python code to do a task,
   ALWAYS run it immediately with bash_execute. Don't show variables like pdf_path = "C:/..." —
   actually execute the code and confirm the file was created.

9. TO CREATE A PDF (fpdf2 is already installed):
   Run Python code with bash_execute. Use this exact syntax (no deprecated params):
   bash_execute("python -c \\"from fpdf import FPDF; pdf = FPDF(); pdf.add_page(); pdf.set_font('Helvetica', size=12); pdf.cell(200, 10, text='Content here', new_x='LMARGIN', new_y='NEXT'); pdf.output('C:/Users/Drugos-Laptop/Desktop/output.pdf'); print('PDF saved')\\"")

10. FILE PATHS on this machine: Desktop is always C:/Users/Drugos-Laptop/Desktop/

You remember every session through patch files in ~/.yahll/sessions/."""

# Format 1: {"name": "tool_name", "arguments": {...}}
_TOOL_CALL_RE = re.compile(
    r'\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*(\{.*?\})\s*\}',
    re.DOTALL,
)

# Format 2: <tool_call>{"name": "...", "arguments": {...}}</tool_call>
_TOOL_CALL_TAG_RE = re.compile(
    r'<tool_call>\s*\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*(\{.*?\})\s*\}\s*</tool_call>',
    re.DOTALL,
)

_ALL_TOOL_REGEXES = [_TOOL_CALL_RE, _TOOL_CALL_TAG_RE]

# Format 3: Python-style — bash_execute("cmd"), read_file("path"), write_file("path", "content")
# Maps tool name → first positional arg name
_PYTHON_CALL_ARG_MAP = {
    "bash_execute": "command",
    "read_file": "path",
    "list_directory": "path",
    "self_read": "relative_path",
    "web_search": "query",
    "web_news": "query",
    "clipboard_write": "text",
}

# Matches: tool_name("single string arg") with single or double quotes
_PYTHON_CALL_RE = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in _PYTHON_CALL_ARG_MAP) + r')\s*\(\s*(["\'])(.*?)\2\s*\)',
    re.DOTALL,
)


def _try_parse_args(raw: str) -> dict | None:
    """Try to parse JSON args, returning None on failure."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _extract_python_tool_calls(content: str) -> list[dict]:
    """Catch Python-style text tool calls like bash_execute('cmd')."""
    calls = []
    seen_names = set()
    for match in _PYTHON_CALL_RE.finditer(content):
        name = match.group(1)
        value = match.group(3)
        if name not in seen_names:
            seen_names.add(name)
            arg_key = _PYTHON_CALL_ARG_MAP[name]
            calls.append({"function": {"name": name, "arguments": {arg_key: value}}})
    return calls


def _extract_text_tool_calls(content: str) -> list[dict]:
    """Some Ollama models return tool calls as JSON text in content. Parse them."""
    calls = []
    seen_names = set()
    for pattern in _ALL_TOOL_REGEXES:
        for match in pattern.finditer(content):
            name = match.group(1)
            args = _try_parse_args(match.group(2))
            if args is not None and name not in seen_names:
                seen_names.add(name)
                calls.append({"function": {"name": name, "arguments": args}})
    return calls


def _strip_tool_call_text(content: str) -> str:
    """Remove all text-based tool call patterns from content."""
    for pattern in _ALL_TOOL_REGEXES:
        content = pattern.sub("", content)
    return content.strip()


class Agent:
    def __init__(self, model: str = "qwen2.5-coder:7b", base_url: str = "http://localhost:11434"):
        self.client = OllamaClient(base_url=base_url, model=model)
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _trim_history(self, max_non_system: int = 20):
        """Keep only the system prompt + last N non-system messages to avoid context overflow."""
        system = [m for m in self.messages if m["role"] == "system"]
        others = [m for m in self.messages if m["role"] != "system"]
        if len(others) > max_non_system:
            others = others[-max_non_system:]
        self.messages = system + others

    def chat(self, user_message: str) -> str:
        """Send a message and return the final text response, executing tools as needed."""
        self._trim_history()
        self.messages.append({"role": "user", "content": user_message})

        for _ in range(10):  # max 10 tool call rounds
            full_content = ""
            tool_calls = []

            for chunk in self.client.chat_stream(self.messages, tools=TOOL_SCHEMAS):
                msg = chunk.get("message", {})
                content = msg.get("content", "")
                if content:
                    full_content += content
                if msg.get("tool_calls"):
                    tool_calls.extend(msg["tool_calls"])

            # Fallback: detect tool calls embedded as text in content
            if not tool_calls and full_content:
                tool_calls = _extract_text_tool_calls(full_content)
                if tool_calls:
                    full_content = _strip_tool_call_text(full_content)
                else:
                    # Last resort: catch Python-style calls like bash_execute("cmd")
                    tool_calls = _extract_python_tool_calls(full_content)
                    if tool_calls:
                        full_content = _PYTHON_CALL_RE.sub("", full_content).strip()

            if tool_calls:
                self.messages.append({
                    "role": "assistant",
                    "content": full_content,
                    "tool_calls": tool_calls,
                })
                tool_results = []
                for tc in tool_calls:
                    fn = tc["function"]
                    name = fn["name"]
                    args = fn.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            args = {}
                    result = dispatch(name, args)
                    tool_results.append(
                        f"<result tool=\"{name}\">\n{json.dumps(result, ensure_ascii=False)}\n</result>"
                    )

                # Send tool results as a single user message — works with all Ollama models
                self.messages.append({
                    "role": "user",
                    "content": "\n\n".join(tool_results),
                })
                continue

            # No tool calls — final answer
            self.messages.append({"role": "assistant", "content": full_content})
            return full_content

        return full_content  # safety exit after 10 rounds

    def clear(self):
        """Reset conversation, keeping system prompt."""
        self.messages = [self.messages[0]]

    def inject_context(self, context: str):
        """Append context to system prompt (used for memory loading)."""
        self.messages[0]["content"] = SYSTEM_PROMPT + "\n\n" + context
