import os
import tempfile
import pytest
from yahll.tools.bash import bash_execute
from yahll.tools.files import read_file, write_file, edit_file
from yahll.tools.search import search_files, list_directory


# --- bash ---
def test_bash_execute_returns_output():
    result = bash_execute("echo hello")
    assert "hello" in result["output"]
    assert result["exit_code"] == 0


def test_bash_execute_captures_nonzero_exit():
    result = bash_execute("exit 1")
    assert result["exit_code"] != 0


# --- files ---
def test_write_and_read_file():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "test.txt")
        write_file(path, "hello world")
        result = read_file(path)
        assert "hello world" in result["content"]


def test_read_file_includes_line_numbers():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "test.txt")
        write_file(path, "line1\nline2\nline3")
        result = read_file(path)
        assert "1\tline1" in result["content"]


def test_read_file_missing_returns_error():
    result = read_file("/nonexistent/path/file.txt")
    assert "error" in result


def test_edit_file_replaces_string():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "test.py")
        write_file(path, "def old_name():\n    pass\n")
        result = edit_file(path, "def old_name():", "def new_name():")
        assert result["success"] is True
        updated = read_file(path)
        assert "new_name" in updated["content"]


def test_edit_file_missing_string_returns_error():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "test.py")
        write_file(path, "def foo(): pass")
        result = edit_file(path, "NOT_HERE", "something")
        assert result["success"] is False


# --- search ---
def test_search_files_finds_pattern():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "main.py")
        write_file(path, "def hello():\n    return 'world'\n")
        result = search_files("def hello", directory=d)
        assert any("main.py" in r for r in result["matches"])


def test_list_directory_returns_entries():
    with tempfile.TemporaryDirectory() as d:
        write_file(os.path.join(d, "a.py"), "")
        write_file(os.path.join(d, "b.py"), "")
        result = list_directory(d)
        assert "a.py" in result["entries"]
        assert "b.py" in result["entries"]
