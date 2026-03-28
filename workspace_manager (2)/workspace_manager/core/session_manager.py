"""
core/session_manager.py

Saves and restores named workspace sessions as JSON files.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict

from core.window_manager import WindowInfo

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, sessions_dir: str = "sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    # ── Persistence helpers ──────────────────────────────────────────────────

    def _path_for(self, name: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)
        return self.sessions_dir / f"{safe}.json"

    # ── Public API ───────────────────────────────────────────────────────────

    def list_sessions(self) -> List[str]:
        """Return all saved session names, sorted by modification time (newest first)."""
        paths = sorted(self.sessions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        return [p.stem for p in paths]

    def save_session(self, name: str, windows: List[WindowInfo]) -> bool:
        """Persist a named session from a list of WindowInfo objects."""
        if not name.strip():
            return False
        data = {
            "name": name,
            "saved_at": datetime.now().isoformat(),
            "windows": [w.to_dict() for w in windows],
        }
        path = self._path_for(name)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info("Session saved: %s (%d windows)", name, len(windows))
            return True
        except Exception as e:
            logger.error("Failed to save session '%s': %s", name, e)
            return False

    def load_session(self, name: str) -> Optional[dict]:
        """Load a session dict by name. Returns None if not found."""
        path = self._path_for(name)
        if not path.exists():
            logger.warning("Session not found: %s", name)
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info("Session loaded: %s", name)
            return data
        except Exception as e:
            logger.error("Failed to load session '%s': %s", name, e)
            return None

    def delete_session(self, name: str) -> bool:
        path = self._path_for(name)
        if path.exists():
            path.unlink()
            logger.info("Session deleted: %s", name)
            return True
        return False

    def match_session_to_live(
        self,
        session_data: dict,
        live_windows: List[WindowInfo],
    ) -> List[WindowInfo]:
        """
        Try to match saved process names against currently open windows.
        Returns a (possibly partial) list of matched live WindowInfo objects.
        """
        saved = session_data.get("windows", [])
        saved_procs = {w["process_name"].lower() for w in saved}
        matched = [w for w in live_windows if w.process_name.lower() in saved_procs]
        logger.info(
            "Session restore: %d/%d windows matched.", len(matched), len(saved)
        )
        return matched
