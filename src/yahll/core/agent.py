import json
import re
from yahll.core.ollama_client import OllamaClient
from yahll.tools.registry import TOOL_SCHEMAS, dispatch

SYSTEM_PROMPT = """You are Yahll, a self-evolving AI coding agent running locally on the user's machine.
You help with code, files, and shell commands. You have access to tools.
Always read files before editing them.
When you run bash commands, show the output to the user.
You remember every session through patch files in ~/.yahll/memory/.
You were built by Drugos and run on an ASUS ROG Strix with RTX 4070, i9-13980HX, 32GB RAM.
You use Ollama locally — zero tokens, zero cost."""

# Regex to detect tool call JSON that qwen sometimes puts in content instead of tool_calls
_TOOL_CALL_RE = re.compile(r'\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*(\{[^}]*\})\s*\}', re.DOTALL)


def _extract_text_tool_calls(content: str) -> list[dict]:
    """Some Ollama models return tool calls as JSON text in content. Parse them."""
    calls = []
    for match in _TOOL_CALL_RE.finditer(content):
        try:
            name = match.group(1)
            args = json.loads(match.group(2))
            calls.append({"function": {"name": name, "arguments": args}})
        except (json.JSONDecodeError, KeyError):
            continue
    return calls


class Agent:
    def __init__(self, model: str = "qwen2.5-coder:7b", base_url: str = "http://localhost:11434"):
        self.client = OllamaClient(base_url=base_url, model=model)
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def chat(self, user_message: str) -> str:
        """Send a message and return the final text response, executing tools as needed."""
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
                    full_content = _TOOL_CALL_RE.sub("", full_content).strip()

            if tool_calls:
                self.messages.append({
                    "role": "assistant",
                    "content": full_content,
                    "tool_calls": tool_calls,
                })
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
                    self.messages.append({
                        "role": "tool",
                        "content": json.dumps(result),
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
