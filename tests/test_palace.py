import os
import pytest
from unittest.mock import patch, MagicMock


# --- init_palace ---

def test_init_palace_creates_directory(tmp_path):
    palace_dir = str(tmp_path / "yahll_palace")
    with patch("yahll.memory.palace.PALACE_PATH", palace_dir):
        from yahll.memory.palace import init_palace
        result = init_palace()
    assert os.path.isdir(palace_dir)
    assert result == palace_dir


# --- load_context ---

def test_load_context_returns_string():
    with patch("yahll.memory.palace.Layer0") as mock_l0, \
         patch("yahll.memory.palace.Layer1") as mock_l1:
        mock_l0.return_value.render.return_value = "## L0\nDrugos"
        mock_l1.return_value.generate.return_value = "## L1\nTop moments"
        from yahll.memory.palace import load_context
        result = load_context()
    assert "L0" in result
    assert "L1" in result


def test_load_context_returns_empty_on_error():
    with patch("yahll.memory.palace.Layer0", side_effect=Exception("no palace")):
        from yahll.memory.palace import load_context
        result = load_context()
    assert result == ""


# --- mine_session ---

def test_mine_session_stores_exchanges(tmp_path):
    palace_dir = str(tmp_path / "palace")
    os.makedirs(palace_dir)
    messages = [
        {"role": "system", "content": "You are Yahll."},
        {"role": "user", "content": "What is 2+2?"},
        {"role": "assistant", "content": "4"},
        {"role": "user", "content": "Thanks"},
        {"role": "assistant", "content": "You're welcome"},
    ]
    mock_col = MagicMock()
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_col

    def fake_thread(target=None, daemon=None):
        t = MagicMock()
        t.start = lambda: target()
        return t

    with patch("yahll.memory.palace.PALACE_PATH", palace_dir), \
         patch("yahll.memory.palace.threading.Thread", side_effect=fake_thread):
        import yahll.memory.palace as palace_mod
        palace_mod._client = mock_client
        from yahll.memory.palace import mine_session
        mine_session(messages)

    assert mock_col.upsert.called


def test_mine_session_skips_system_messages(tmp_path):
    palace_dir = str(tmp_path / "palace")
    os.makedirs(palace_dir)
    messages = [
        {"role": "system", "content": "System prompt"},
    ]
    mock_col = MagicMock()
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_col

    def fake_thread(target=None, daemon=None):
        t = MagicMock()
        t.start = lambda: target()
        return t

    with patch("yahll.memory.palace.PALACE_PATH", palace_dir), \
         patch("yahll.memory.palace.threading.Thread", side_effect=fake_thread):
        import yahll.memory.palace as palace_mod
        palace_mod._client = mock_client
        from yahll.memory.palace import mine_session
        mine_session(messages)

    mock_col.upsert.assert_not_called()


# --- search ---

def test_search_returns_results():
    mock_results = {
        "documents": [["You asked about 2+2", "We debugged agent.py"]],
        "metadatas": [[{"wing": "yahll"}, {"wing": "yahll"}]],
        "distances": [[0.1, 0.2]],
    }
    mock_col = MagicMock()
    mock_col.query.return_value = mock_results
    mock_client = MagicMock()
    mock_client.get_collection.return_value = mock_col

    with patch("yahll.memory.palace._get_client", return_value=mock_client):
        from yahll.memory.palace import search
        results = search("2+2")

    assert len(results) == 2
    assert "2+2" in results[0]


def test_search_returns_empty_on_no_palace():
    with patch("yahll.memory.palace._get_client", side_effect=Exception("no db")):
        from yahll.memory.palace import search
        results = search("anything")
    assert results == []
