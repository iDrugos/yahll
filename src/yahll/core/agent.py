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

## YOUR ONLY JOB: USE TOOLS. DO NOT EXPLAIN. DO NOT SHOW CODE. JUST DO IT.

WHEN THE USER ASKS YOU TO DO SOMETHING:
- Call the tool. Immediately. No preamble.
- Do NOT show a code block and say "run this".
- Do NOT say "here is the code", "you can run", "let me show you", "here's how".
- Do NOT list steps before acting. Just act.
- After the tool runs, give ONE short sentence confirming what happened.

WRONG (never do this):
  "Here is the Python code to create the file:
   ```python
   import os
   os.makedirs(...)
   ```
   Run this to create the directory."

RIGHT (always do this):
  [call bash_execute immediately with the command]
  "Done. Created Example Site folder with index.html on your Desktop."

## TOOL USAGE RULES:

1. CREATE FILES/FOLDERS → bash_execute immediately. No description first.
2. INSTALL SOFTWARE → bash_execute("winget install <Name> --accept-package-agreements --accept-source-agreements")
3. INSTALL PYTHON PACKAGES → bash_execute("pip install <package>")
4. RUN PYTHON CODE → bash_execute("python -c \"<code>\"") — run it, don't show it
5. READ FILES before editing → read_file first, always
6. EDIT FILES → read_file → then write_file or edit_file
7. SEARCH WEB → web_search, then summarize results
8. OPEN BROWSER → browser_open(url)
9. OPEN APP → open_app(name)
10. SCREENSHOT → screenshot() then describe what you see

## FILE PATHS:
- Desktop: C:/Users/Drugos-Laptop/Desktop/
- Home: C:/Users/Drugos-Laptop/

## CREATING A FOLDER + FILE EXAMPLE:
User: "make a folder called Test on desktop with index.html"
You: [call bash_execute("python -c \"import os; os.makedirs('C:/Users/Drugos-Laptop/Desktop/Test', exist_ok=True); open('C:/Users/Drugos-Laptop/Desktop/Test/index.html','w').write('<h1>Test</h1>'); print('done')\"")]
Then: "Created. Test/ folder with index.html is on your Desktop."

## CREATING A PDF:
bash_execute("python -c \"from fpdf import FPDF; pdf=FPDF(); pdf.add_page(); pdf.set_font('Helvetica',size=12); pdf.cell(200,10,text='Content',new_x='LMARGIN',new_y='NEXT'); pdf.output('C:/Users/Drugos-Laptop/Desktop/output.pdf'); print('PDF saved')\"")

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

    def stream_chat(self, user_message: str, on_token=None, on_tool=None):
        """
        Like chat() but streams tokens live via callbacks.
        on_token(text) — called for each text chunk as it arrives
        on_tool(name, result) — called when a tool is executed
        Returns the full final response string.
        """
        self._trim_history()
        self.messages.append({"role": "user", "content": user_message})

        for _ in range(10):
            full_content = ""
            tool_calls = []
            streamed_any = False

            for chunk in self.client.chat_stream(self.messages, tools=TOOL_SCHEMAS):
                msg = chunk.get("message", {})
                content = msg.get("content", "")
                if content:
                    full_content += content
                    if on_token and not msg.get("tool_calls"):
                        on_token(content)
                        streamed_any = True
                if msg.get("tool_calls"):
                    tool_calls.extend(msg["tool_calls"])

            # Fallback: detect tool calls in content text
            if not tool_calls and full_content:
                tool_calls = _extract_text_tool_calls(full_content)
                if tool_calls:
                    full_content = _strip_tool_call_text(full_content)
                else:
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
                    if on_tool:
                        on_tool(name, result)
                    tool_results.append(
                        f"<result tool=\"{name}\">\n{json.dumps(result, ensure_ascii=False)}\n</result>"
                    )
                self.messages.append({
                    "role": "user",
                    "content": "\n\n".join(tool_results),
                })
                continue

            self.messages.append({"role": "assistant", "content": full_content})
            return full_content

        return full_content  # safety exit after 10 rounds

    def clear(self):
        """Reset conversation, keeping system prompt."""
        self.messages = [self.messages[0]]

    def inject_context(self, context: str):
        """Append context to system prompt (used for memory loading)."""
        self.messages[0]["content"] = SYSTEM_PROMPT + "\n\n" + context
