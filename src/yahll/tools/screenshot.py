import os
import time
from datetime import datetime


def screenshot(save_path: str = "") -> dict:
    """Take a screenshot and save it. Returns the file path."""
    try:
        from PIL import ImageGrab
    except ImportError:
        return {"error": "Pillow not installed. Run: pip install Pillow"}

    if not save_path:
        desktop = os.path.expanduser("~/Desktop")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        save_path = os.path.join(desktop, f"yahll-screenshot-{timestamp}.png")

    try:
        img = ImageGrab.grab()
        img.save(save_path)
        return {
            "path": save_path,
            "width": img.width,
            "height": img.height,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}
