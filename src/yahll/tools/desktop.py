"""
Desktop control tools for Yahll — mouse, keyboard, apps, browser.
Requires: pyautogui, pygetwindow (pip install pyautogui pygetwindow)
"""
import subprocess
import webbrowser
import os


def _pyautogui():
    try:
        import pyautogui
        pyautogui.FAILSAFE = True  # move mouse to top-left corner to abort
        pyautogui.PAUSE = 0.05
        return pyautogui
    except ImportError:
        return None


def mouse_move(x: int, y: int) -> dict:
    """Move the mouse cursor to screen coordinates (x, y)."""
    pg = _pyautogui()
    if pg is None:
        return {"error": "pyautogui not installed. Run: pip install pyautogui"}
    try:
        pg.moveTo(x, y, duration=0.2)
        return {"moved_to": {"x": x, "y": y}}
    except Exception as e:
        return {"error": str(e)}


def mouse_click(x: int, y: int, button: str = "left", clicks: int = 1) -> dict:
    """Click the mouse at screen coordinates (x, y)."""
    pg = _pyautogui()
    if pg is None:
        return {"error": "pyautogui not installed. Run: pip install pyautogui"}
    try:
        pg.click(x, y, button=button, clicks=clicks, interval=0.1)
        return {"clicked": {"x": x, "y": y, "button": button, "clicks": clicks}}
    except Exception as e:
        return {"error": str(e)}


def keyboard_type(text: str, interval: float = 0.02) -> dict:
    """Type text using the keyboard at the current cursor position."""
    pg = _pyautogui()
    if pg is None:
        return {"error": "pyautogui not installed. Run: pip install pyautogui"}
    try:
        pg.typewrite(text, interval=interval)
        return {"typed": len(text), "chars": text[:80] + ("..." if len(text) > 80 else "")}
    except Exception as e:
        return {"error": str(e)}


def keyboard_hotkey(keys: list) -> dict:
    """
    Press a keyboard hotkey combination.
    Examples: ["ctrl", "c"], ["alt", "tab"], ["win", "d"], ["ctrl", "shift", "esc"]
    """
    pg = _pyautogui()
    if pg is None:
        return {"error": "pyautogui not installed. Run: pip install pyautogui"}
    try:
        pg.hotkey(*keys)
        return {"hotkey": "+".join(keys)}
    except Exception as e:
        return {"error": str(e)}


def get_screen_size() -> dict:
    """Return the width and height of the screen in pixels."""
    pg = _pyautogui()
    if pg is None:
        return {"error": "pyautogui not installed. Run: pip install pyautogui"}
    try:
        w, h = pg.size()
        return {"width": w, "height": h}
    except Exception as e:
        return {"error": str(e)}


def get_active_window() -> dict:
    """Return the title of the currently focused window."""
    try:
        import pygetwindow as gw
        win = gw.getActiveWindow()
        if win:
            return {"title": win.title, "left": win.left, "top": win.top,
                    "width": win.width, "height": win.height}
        return {"title": None}
    except ImportError:
        # Fallback: use ctypes on Windows
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            buf = ctypes.create_unicode_buffer(512)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, 512)
            return {"title": buf.value}
        except Exception as e:
            return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def browser_open(url: str) -> dict:
    """Open a URL in the default web browser."""
    try:
        webbrowser.open(url)
        return {"opened": url}
    except Exception as e:
        return {"error": str(e)}


def open_app(name_or_path: str) -> dict:
    """
    Launch an application by name or full path.
    Examples: "notepad", "calc", "C:/Program Files/app.exe"
    Uses 'start' on Windows so it does not block.
    """
    try:
        if os.path.isabs(name_or_path) or name_or_path.endswith(".exe"):
            subprocess.Popen([name_or_path], shell=False)
        else:
            subprocess.Popen(f"start {name_or_path}", shell=True)
        return {"launched": name_or_path}
    except Exception as e:
        return {"error": str(e)}
