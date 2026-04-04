import pytest
from unittest.mock import patch
from yahll.core.agent import Agent


def _text_chunk(text, done=True):
    return {"message": {"role": "assistant", "content": text}, "done": done}


def _tool_chunk(name, args):
    return {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"function": {"name": name, "arguments": args}}],
        },
        "done": True,
    }


def test_agent_initializes_with_system_prompt():
    agent = Agent()
    assert agent.messages[0]["role"] == "system"
    assert "Yahll" in agent.messages[0]["content"]


def test_agent_adds_user_message():
    agent = Agent()
    with patch.object(agent.client, "chat_stream", return_value=iter([_text_chunk("Hello!")])):
        agent.chat("hi")
    assert any(m["role"] == "user" and m["content"] == "hi" for m in agent.messages)


def test_agent_returns_text_response():
    agent = Agent()
    with patch.object(agent.client, "chat_stream", return_value=iter([_text_chunk("I am Yahll")])):
        result = agent.chat("who are you?")
    assert result == "I am Yahll"


def test_agent_dispatches_tool_call():
    agent = Agent()
    with patch.object(agent.client, "chat_stream", side_effect=[
        iter([_tool_chunk("bash_execute", {"command": "echo hi"})]),
        iter([_text_chunk("Done.")]),
    ]):
        with patch("yahll.core.agent.dispatch", return_value={"output": "hi\n", "exit_code": 0}) as mock_dispatch:
            result = agent.chat("run echo hi")
    mock_dispatch.assert_called_once_with("bash_execute", {"command": "echo hi"})
    assert result == "Done."


def test_agent_clear_resets_messages():
    agent = Agent()
    with patch.object(agent.client, "chat_stream", return_value=iter([_text_chunk("ok")])):
        agent.chat("hello")
    assert len(agent.messages) > 1
    agent.clear()
    assert len(agent.messages) == 1
    assert agent.messages[0]["role"] == "system"
