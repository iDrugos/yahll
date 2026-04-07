import pyperclip


def clipboard_read() -> dict:
    """Read current clipboard content."""
    try:
        content = pyperclip.paste()
        return {"content": content, "length": len(content)}
    except Exception as e:
        return {"content": "", "error": str(e)}


def clipboard_write(text: str) -> dict:
    """Write text to clipboard."""
    try:
        pyperclip.copy(text)
        return {"success": True, "length": len(text)}
    except Exception as e:
        return {"success": False, "error": str(e)}
