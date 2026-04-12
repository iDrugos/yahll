from yahll.tools.bash import bash_execute
from yahll.tools.files import read_file, write_file, edit_file, edit_files
from yahll.tools.search import search_files, list_directory
from yahll.tools.self_tools import self_read, self_write, self_list
from yahll.tools.web_search import web_search, web_news
from yahll.tools.clipboard import clipboard_read, clipboard_write
from yahll.tools.screenshot import screenshot
from yahll.memory.knowledge_base import load_skill
from yahll.tools.desktop import (
    mouse_move, mouse_click, keyboard_type, keyboard_hotkey,
    get_screen_size, get_active_window, browser_open, open_app,
)

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "bash_execute",
            "description": "Execute a shell command and return stdout, stderr, exit code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file with line numbers. Always use before editing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file (creates or overwrites).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace a specific string in a file (first occurrence only).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_string": {"type": "string"},
                    "new_string": {"type": "string"},
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_files",
            "description": "Apply multiple edits across multiple files in one call. Pass a list of {path, old_string, new_string} objects.",
            "parameters": {
                "type": "object",
                "properties": {
                    "edits": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "old_string": {"type": "string"},
                                "new_string": {"type": "string"},
                            },
                            "required": ["path", "old_string", "new_string"],
                        },
                    }
                },
                "required": ["edits"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for a regex pattern across files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "directory": {"type": "string", "default": "."},
                    "file_glob": {"type": "string", "default": "*.py"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and directories at a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "default": "."}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "self_read",
            "description": "Read a file from Yahll's own source code. Path relative to src/yahll/ e.g. 'tools/bash.py'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_path": {"type": "string"}
                },
                "required": ["relative_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "self_write",
            "description": "Write to a file in Yahll's own source. Creates snapshot backup first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["relative_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "self_list",
            "description": "List all Python files in Yahll's own source tree.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web using DuckDuckGo. No API key needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_news",
            "description": "Search for recent news using DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "News search query"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clipboard_read",
            "description": "Read the current clipboard content.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clipboard_write",
            "description": "Write text to the clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to copy to clipboard"}
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "load_skill",
            "description": (
                "Load a skill file from the knowledge base (A Taste of Knowlegement). "
                "Use this when you need domain knowledge: ML, algorithms, system design, LLMs, "
                "dev resources, research papers, etc. Pass the skill name or a keyword — fuzzy match is supported."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": (
                            "Skill name or keyword. Examples: 'ml', 'system-design', 'algorithms', "
                            "'llms', 'developer-resources', 'oss-alternatives', 'research-papers'."
                        ),
                    }
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_move",
            "description": "Move the mouse cursor to screen coordinates (x, y).",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Horizontal pixel position"},
                    "y": {"type": "integer", "description": "Vertical pixel position"},
                },
                "required": ["x", "y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_click",
            "description": "Click the mouse at screen coordinates. button: left/right/middle. clicks: 1 or 2.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "button": {"type": "string", "default": "left"},
                    "clicks": {"type": "integer", "default": 1},
                },
                "required": ["x", "y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "keyboard_type",
            "description": "Type text using the keyboard at the current cursor position.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"},
                    "interval": {"type": "number", "default": 0.02, "description": "Delay between keystrokes in seconds"},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "keyboard_hotkey",
            "description": "Press a keyboard hotkey combination. E.g. ['ctrl','c'], ['alt','tab'], ['win','d'].",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of keys to press together, e.g. ['ctrl', 'c']",
                    }
                },
                "required": ["keys"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_screen_size",
            "description": "Return the screen resolution in pixels (width x height).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_active_window",
            "description": "Return the title and position of the currently focused window.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_open",
            "description": "Open a URL in the default web browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to open"}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Launch an application by name or full path. E.g. 'notepad', 'calc', 'C:/path/to/app.exe'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name_or_path": {"type": "string", "description": "App name or executable path"}
                },
                "required": ["name_or_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "screenshot",
            "description": "Take a screenshot of the current screen and save it as a PNG file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "save_path": {
                        "type": "string",
                        "description": "Full path to save the PNG. Defaults to Desktop with timestamp.",
                        "default": "",
                    }
                },
                "required": [],
            },
        },
    },
]

TOOL_DISPATCH = {
    "bash_execute": bash_execute,
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "edit_files": edit_files,
    "search_files": search_files,
    "list_directory": list_directory,
    "self_read": self_read,
    "self_write": self_write,
    "self_list": self_list,
    "web_search": web_search,
    "web_news": web_news,
    "clipboard_read": clipboard_read,
    "clipboard_write": clipboard_write,
    "load_skill": load_skill,
    "screenshot": screenshot,
    "mouse_move": mouse_move,
    "mouse_click": mouse_click,
    "keyboard_type": keyboard_type,
    "keyboard_hotkey": keyboard_hotkey,
    "get_screen_size": get_screen_size,
    "get_active_window": get_active_window,
    "browser_open": browser_open,
    "open_app": open_app,
}


def dispatch(name: str, arguments: dict) -> dict:
    """Call a tool by name with given arguments."""
    fn = TOOL_DISPATCH.get(name)
    if fn is None:
        return {"error": f"Unknown tool: {name}"}
    return fn(**arguments)
