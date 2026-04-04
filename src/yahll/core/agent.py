import json
from yahll.core.ollama_client import OllamaClient
from yahll.tools.registry import TOOL_SCHEMAS, dispatch

SYSTEM_PROMPT = """You are Yahll, a self-evolving AI coding agent running locally on the user's machine.
You help with code, files, and shell commands. You have access to tools.
Always read files before editing them.
When you run bash commands, show the output to the user.
You remember every session through patch files in ~/.yahll/memory/.
You were built by Drugos and run on an ASUS ROG Strix with RTX 4070, i9-13980HX, 32GB RAM.
You use Ollama locally — zero tokens, zero cost."""


class Agent:
    def __init__(self, model: str = "qwen2.5-coder:7b", base_url: str = "http://localhost:11434"):
        self.client = OllamaClient(base_url=base_url, model=model)
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def chat(self, user_message: str) -> str:
        """Send a message and return the final text response, executing tools as needed."""
        self.messages.append({"role": "user", "content": user_message})

        while True:
            full_content = ""
            tool_calls = []

            for chunk in self.client.chat_stream(self.messages, tools=TOOL_SCHEMAS):
                msg = chunk.get("message", {})
                content = msg.get("content", "")
                if content:
                    full_content += content
                if msg.get("tool_calls"):
                    tool_calls.extend(msg["tool_calls"])

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
                        args = json.loads(args)
                    result = dispatch(name, args)
                    self.messages.append({
                        "role": "tool",
                        "content": json.dumps(result),
                    })
                continue

            self.messages.append({"role": "assistant", "content": full_content})
            return full_content

    def clear(self):
        """Reset conversation, keeping system prompt."""
        self.messages = [self.messages[0]]

    def inject_context(self, context: str):
        """Append context to system prompt (used for memory loading)."""
        self.messages[0]["content"] = SYSTEM_PROMPT + "\n\n" + context
