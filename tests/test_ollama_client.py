import pytest
from unittest.mock import patch, MagicMock
from yahll.core.ollama_client import OllamaClient


def test_client_initializes_with_defaults():
    client = OllamaClient()
    assert client.base_url == "http://localhost:11434"
    assert client.model == "qwen2.5-coder:7b"


def test_client_accepts_custom_model():
    client = OllamaClient(model="llama3.2:3b")
    assert client.model == "llama3.2:3b"


def test_build_payload_includes_model_and_messages():
    client = OllamaClient()
    messages = [{"role": "user", "content": "hello"}]
    payload = client._build_payload(messages, tools=None)
    assert payload["model"] == "qwen2.5-coder:7b"
    assert payload["messages"] == messages
    assert payload["stream"] is True


def test_build_payload_includes_tools_when_provided():
    client = OllamaClient()
    tools = [{"type": "function", "function": {"name": "bash_execute"}}]
    payload = client._build_payload([{"role": "user", "content": "hi"}], tools=tools)
    assert payload["tools"] == tools


def test_is_running_returns_false_when_unreachable():
    client = OllamaClient(base_url="http://localhost:19999")
    assert client.is_running() is False
