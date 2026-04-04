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
        with httpx.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120.0,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.strip():
                    yield json.loads(line)

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
