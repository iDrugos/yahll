"""
Yahll system tray + global hotkey.
Tray icon lives in the taskbar — right-click to open/quit.
Win+Y hotkey opens the web UI from anywhere.
"""
import threading
import webbrowser

SERVER_URL = "http://localhost:7777"


def _make_icon():
    """Generate a cyan Y icon using Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle
    draw.ellipse([2, 2, size - 2, size - 2], fill=(10, 10, 20, 255))
    draw.ellipse([2, 2, size - 2, size - 2], outline=(0, 212, 255, 200), width=2)

    # Draw Y shape
    cx = size // 2
    # Left arm
    draw.line([14, 12, cx, 34], fill=(0, 212, 255, 255), width=5)
    # Right arm
    draw.line([size - 14, 12, cx, 34], fill=(0, 212, 255, 255), width=5)
    # Stem
    draw.line([cx, 34, cx, size - 12], fill=(0, 212, 255, 255), width=5)

    return img


def _open_ui():
    webbrowser.open(SERVER_URL)


def run_tray(on_quit):
    """Start the system tray icon. Blocks — run in a thread."""
    try:
        import pystray
    except ImportError:
        print("[tray] pystray not installed — tray icon disabled.")
        return

    icon_img = _make_icon()

    menu = pystray.Menu(
        pystray.MenuItem("Open Yahll", lambda icon, item: _open_ui(), default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", lambda icon, item: (on_quit(), icon.stop())),
    )

    icon = pystray.Icon("Yahll", icon_img, "Yahll — Local AI Agent", menu)
    icon.run()


def run_hotkey():
    """Register Win+Y global hotkey to open the UI. Non-blocking."""
    try:
        import keyboard
        keyboard.add_hotkey("win+y", _open_ui, suppress=False)
        # Keep the hotkey thread alive without blocking
        keyboard.wait()
    except ImportError:
        print("[hotkey] keyboard package not installed — Win+Y disabled.")
    except Exception as e:
        print(f"[hotkey] Could not register Win+Y: {e}")


def start_hotkey_thread():
    t = threading.Thread(target=run_hotkey, daemon=True, name="yahll-hotkey")
    t.start()
    return t
