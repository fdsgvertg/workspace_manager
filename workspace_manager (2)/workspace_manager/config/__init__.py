"""Config package — loads and provides app configuration."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.json"

DEFAULTS = {
    "refresh_interval_ms": 3000,
    "voice_backend": "vosk",          # "vosk" | "whisper"
    "vosk_model_path": "models/vosk-model-small-en-us",
    "whisper_model": "tiny",
    "embedding_model": "all-MiniLM-L6-v2",
    "sessions_dir": "sessions",
    "theme": "dark",
    "window_min_title_len": 1,
    "auto_group": True,
    "confirm_close": True,
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user = json.load(f)
            cfg = {**DEFAULTS, **user}
            logger.info("Config loaded from %s", CONFIG_PATH)
            return cfg
        except Exception as e:
            logger.warning("Failed to load config (%s), using defaults.", e)
    return dict(DEFAULTS)


def save_config(cfg: dict) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        logger.error("Failed to save config: %s", e)


CONFIG = load_config()
