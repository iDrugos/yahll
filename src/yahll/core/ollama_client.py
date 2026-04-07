import httpx
import json
from typing import Iterator


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5-coder:7b"):
        self.base_url = base_url
        self.model = model

    def _build_payload(self, messages: list, tools: list | None) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools
        return payload

    def chat_stream(self, messages: list, tools: list | None = None) -> Iterator[dict]:
        """Stream chat response from Ollama. Yields parsed JSON chunks."""
        payload = self._build_payload(messages, tools)
        try:
            with httpx.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=180.0,
            ) as response:
                if response.status_code == 500:
                    # Context overflow — yield an error message chunk
                    yield {"message": {"content": "[ERROR: Ollama returned 500 — context may be too long. Type /clear to reset.]", "role": "assistant"}}
                    return
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.strip():
                        yield json.loads(line)
        except httpx.HTTPStatusError as e:
            yield {"message": {"content": f"[ERROR: {e.response.status_code} from Ollama. Try /clear to reset context.]", "role": "assistant"}}

    def list_models(self) -> list[str]:
        """Return list of available Ollama model names."""
        response = httpx.get(f"{self.base_url}/api/tags", timeout=10.0)
        response.raise_for_status()
        return [m["name"] for m in response.json().get("models", [])]

    def is_running(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            httpx.get(f"{self.base_url}/api/tags", timeout=3.0)
            return True
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
