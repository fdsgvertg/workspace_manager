"""
core/window_manager.py

Detects and controls open Windows using pywin32.
Falls back to demo data on non-Windows or missing pywin32.
"""

import sys
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

# ── Platform detection ──────────────────────────────────────────────────────
IS_WINDOWS = sys.platform == "win32"

try:
    import win32gui
    import win32process
    import win32con
    import win32api
    import psutil
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logger.warning("pywin32 / psutil not available — running in demo mode.")


# ── Data model ───────────────────────────────────────────────────────────────

GROUPS = ["Work", "Study", "Entertainment", "Other"]

WORK_KEYWORDS = [
    "code", "visual studio", "vscode", "pycharm", "intellij", "sublime",
    "slack", "teams", "outlook", "notion", "jira", "github", "gitlab",
    "terminal", "cmd", "powershell", "explorer", "excel", "word", "powerpoint",
    "zoom", "meet", "figma", "postman", "docker", "kubernetes", "bash",
]

STUDY_KEYWORDS = [
    "tutorial", "documentation", "docs", "stack overflow", "youtube",
    "coursera", "udemy", "edx", "khan", "wikipedia", "pdf", "lecture",
    "textbook", "learn", "course", "university",
]

ENTERTAINMENT_KEYWORDS = [
    "spotify", "netflix", "steam", "discord", "twitch", "reddit",
    "instagram", "twitter", "x.com", "tiktok", "vlc", "media player",
    "prime video", "hulu", "game", "minecraft",
]

PROCESS_EMOJI = {
    "code": "🖥️",
    "chrome": "🌐",
    "firefox": "🦊",
    "edge": "🌐",
    "slack": "💬",
    "discord": "🎮",
    "spotify": "🎵",
    "steam": "🎮",
    "outlook": "📧",
    "teams": "👥",
    "explorer": "📁",
    "cmd": "⌨️",
    "powershell": "⌨️",
    "python": "🐍",
    "pycharm": "🐍",
    "notepad": "📝",
    "word": "📄",
    "excel": "📊",
    "powerpoint": "📊",
    "zoom": "📹",
    "vlc": "🎬",
    "default": "🪟",
}


@dataclass
class WindowInfo:
    hwnd: int
    title: str
    process_name: str
    pid: int
    group: str = "Other"
    emoji: str = "🪟"
    is_minimized: bool = False
    position: tuple = field(default_factory=lambda: (0, 0, 800, 600))

    def to_dict(self) -> dict:
        return {
            "hwnd": self.hwnd,
            "title": self.title,
            "process_name": self.process_name,
            "pid": self.pid,
            "group": self.group,
        }


# ── Grouping heuristic ───────────────────────────────────────────────────────

def classify_window(title: str, process_name: str) -> str:
    text = (title + " " + process_name).lower()
    if any(k in text for k in WORK_KEYWORDS):
        return "Work"
    if any(k in text for k in STUDY_KEYWORDS):
        return "Study"
    if any(k in text for k in ENTERTAINMENT_KEYWORDS):
        return "Entertainment"
    return "Other"


def get_emoji(process_name: str) -> str:
    proc = process_name.lower().replace(".exe", "")
    for key, emoji in PROCESS_EMOJI.items():
        if key in proc:
            return emoji
    return PROCESS_EMOJI["default"]


# ── Real window enumeration (Windows) ───────────────────────────────────────

def _enum_windows_real() -> List[WindowInfo]:
    results: List[WindowInfo] = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if not title or len(title.strip()) == 0:
            return
        # Skip taskbar, shells, etc.
        if title in ("Program Manager", "Windows Input Experience"):
            return

        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                proc = psutil.Process(pid)
                proc_name = proc.name()
            except Exception:
                proc_name = "unknown.exe"

            is_minimized = win32gui.IsIconic(hwnd)
            try:
                rect = win32gui.GetWindowRect(hwnd)
            except Exception:
                rect = (0, 0, 800, 600)

            group = classify_window(title, proc_name)
            emoji = get_emoji(proc_name)

            results.append(WindowInfo(
                hwnd=hwnd,
                title=title,
                process_name=proc_name,
                pid=pid,
                group=group,
                emoji=emoji,
                is_minimized=is_minimized,
                position=rect,
            ))
        except Exception as e:
            logger.debug("Skipping hwnd %s: %s", hwnd, e)

    win32gui.EnumWindows(callback, None)
    return results


# ── Demo mode ────────────────────────────────────────────────────────────────

DEMO_WINDOWS = [
    WindowInfo(1001, "main.py — workspace_manager [Visual Studio Code]", "Code.exe",      1001, "Work",          "🖥️"),
    WindowInfo(1002, "Python Tutorial — YouTube",                         "chrome.exe",    1002, "Study",         "🌐"),
    WindowInfo(1003, "Slack — #general",                                  "slack.exe",     1003, "Work",          "💬"),
    WindowInfo(1004, "Spotify — Now Playing",                             "spotify.exe",   1004, "Entertainment", "🎵"),
    WindowInfo(1005, "Stack Overflow — How to use pywin32",               "firefox.exe",   1005, "Study",         "🦊"),
    WindowInfo(1006, "Discord — My Server",                               "discord.exe",   1006, "Entertainment", "🎮"),
    WindowInfo(1007, "Microsoft Teams — Meeting",                         "teams.exe",     1007, "Work",          "👥"),
    WindowInfo(1008, "File Explorer — Documents",                         "explorer.exe",  1008, "Work",          "📁"),
    WindowInfo(1009, "Netflix — Currently Watching",                      "chrome.exe",    1009, "Entertainment", "🌐"),
    WindowInfo(1010, "GitHub — Pull Requests",                            "chrome.exe",    1010, "Work",          "🌐"),
    WindowInfo(1011, "Deep Learning Lecture — Coursera",                  "chrome.exe",    1011, "Study",         "🌐"),
    WindowInfo(1012, "Notepad — notes.txt",                               "notepad.exe",   1012, "Work",          "📝"),
]


# ── Public API ───────────────────────────────────────────────────────────────

class WindowManager:
    """
    Public interface for listing and controlling windows.
    Auto-detects Windows vs demo mode.
    """

    def __init__(self):
        self._demo = not (IS_WINDOWS and WIN32_AVAILABLE)
        if self._demo:
            logger.info("WindowManager: demo mode active.")
        else:
            logger.info("WindowManager: live mode (pywin32).")

    @property
    def is_demo(self) -> bool:
        return self._demo

    def get_windows(self) -> List[WindowInfo]:
        if self._demo:
            return list(DEMO_WINDOWS)
        try:
            return _enum_windows_real()
        except Exception as e:
            logger.error("EnumWindows failed: %s", e)
            return []

    def focus_window(self, win: WindowInfo) -> bool:
        if self._demo:
            logger.info("[DEMO] Focus: %s", win.title)
            return True
        try:
            if win32gui.IsIconic(win.hwnd):
                win32gui.ShowWindow(win.hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(win.hwnd)
            return True
        except Exception as e:
            logger.warning("focus_window failed: %s", e)
            return False

    def minimize_window(self, win: WindowInfo) -> bool:
        if self._demo:
            logger.info("[DEMO] Minimize: %s", win.title)
            return True
        try:
            win32gui.ShowWindow(win.hwnd, win32con.SW_MINIMIZE)
            return True
        except Exception as e:
            logger.warning("minimize_window failed: %s", e)
            return False

    def close_window(self, win: WindowInfo) -> bool:
        if self._demo:
            logger.info("[DEMO] Close: %s", win.title)
            return True
        try:
            win32gui.PostMessage(win.hwnd, win32con.WM_CLOSE, 0, 0)
            return True
        except Exception as e:
            logger.warning("close_window failed: %s", e)
            return False
