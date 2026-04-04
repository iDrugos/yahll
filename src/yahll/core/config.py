import os
import yaml

YAHLL_HOME = os.path.expanduser("~/.yahll")
CONFIG_PATH = os.path.join(YAHLL_HOME, "config.yaml")

DEFAULT_CONFIG = {
    "model": "qwen2.5-coder:7b",
    "ollama_url": "http://localhost:11434",
    "max_context_messages": 50,
    "auto_save_patches": True,
}


def load_config() -> dict:
    """Load config from ~/.yahll/config.yaml, creating defaults if missing."""
    os.makedirs(YAHLL_HOME, exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_PATH, "r") as f:
        loaded = yaml.safe_load(f) or {}
    return {**DEFAULT_CONFIG, **loaded}


def save_config(config: dict):
    """Save config to ~/.yahll/config.yaml."""
    os.makedirs(YAHLL_HOME, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
