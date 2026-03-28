"""
ui/main_window.py

WorkspaceAI — dark glassmorphic PyQt6 dashboard.
"""

import logging
from typing import List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea,
    QFrame, QComboBox, QDialog, QDialogButtonBox,
    QInputDialog, QMessageBox, QSizePolicy, QGridLayout,
    QStatusBar, QToolButton, QMenu,
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation,
    QEasingCurve, QSize,
)
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QAction

from core.window_manager import WindowManager, WindowInfo, GROUPS
from core.session_manager import SessionManager
from ai.engine import AIEngine
from voice.processor import VoiceProcessor
from config import CONFIG

logger = logging.getLogger(__name__)


# ── Stylesheet ────────────────────────────────────────────────────────────────

STYLESHEET = """
QMainWindow, QWidget#central {
    background-color: #0d0f14;
}

/* ── Search bar ── */
QLineEdit#search_bar {
    background: rgba(255,255,255,0.05);
    border: 1.5px solid rgba(255,255,255,0.12);
    border-radius: 12px;
    color: #e8eaf0;
    font-size: 15px;
    padding: 10px 16px;
    selection-background-color: #3d5afe;
}
QLineEdit#search_bar:focus {
    border-color: #3d5afe;
    background: rgba(61,90,254,0.08);
}
QLineEdit#search_bar::placeholder {
    color: rgba(255,255,255,0.3);
}

/* ── Toolbar buttons ── */
QPushButton.toolbar_btn {
    background: rgba(255,255,255,0.06);
    border: 1.5px solid rgba(255,255,255,0.10);
    border-radius: 10px;
    color: #c8ccd8;
    font-size: 13px;
    padding: 8px 16px;
}
QPushButton.toolbar_btn:hover {
    background: rgba(255,255,255,0.12);
    border-color: rgba(255,255,255,0.2);
    color: #ffffff;
}
QPushButton.toolbar_btn:pressed {
    background: rgba(61,90,254,0.2);
}
QPushButton#voice_btn {
    background: rgba(255,255,255,0.06);
    border: 1.5px solid rgba(255,255,255,0.10);
    border-radius: 10px;
    color: #c8ccd8;
    font-size: 18px;
    padding: 8px 14px;
    min-width: 44px;
}
QPushButton#voice_btn:hover {
    background: rgba(255,255,255,0.12);
    color: #ffffff;
}
QPushButton#voice_btn[listening="true"] {
    background: rgba(229,57,53,0.25);
    border-color: #e53935;
    color: #ff5252;
}

/* ── Group filter tabs ── */
QPushButton.group_tab {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 0px;
    color: rgba(255,255,255,0.4);
    font-size: 13px;
    font-weight: 600;
    padding: 8px 18px;
    letter-spacing: 0.5px;
}
QPushButton.group_tab:hover {
    color: rgba(255,255,255,0.75);
}
QPushButton.group_tab[active="true"] {
    color: #ffffff;
    border-bottom-color: #3d5afe;
}

/* ── Window cards ── */
QFrame.win_card {
    background: rgba(255,255,255,0.045);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    margin: 4px;
}
QFrame.win_card:hover {
    background: rgba(255,255,255,0.075);
    border-color: rgba(255,255,255,0.15);
}

/* ── Card labels ── */
QLabel.win_title {
    color: #e8eaf0;
    font-size: 13px;
    font-weight: 600;
}
QLabel.win_proc {
    color: rgba(255,255,255,0.40);
    font-size: 11px;
}
QLabel.win_emoji {
    font-size: 22px;
}

/* ── Card action buttons ── */
QPushButton.card_btn {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 7px;
    color: rgba(255,255,255,0.55);
    font-size: 11px;
    padding: 3px 9px;
    min-height: 22px;
}
QPushButton.card_btn:hover {
    background: rgba(255,255,255,0.14);
    color: #ffffff;
}
QPushButton.card_btn#close_btn:hover {
    background: rgba(229,57,53,0.25);
    border-color: #e53935;
    color: #ff5252;
}

/* ── Group dropdown on card ── */
QComboBox.group_combo {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 7px;
    color: rgba(255,255,255,0.55);
    font-size: 11px;
    padding: 3px 6px;
    min-height: 22px;
}
QComboBox.group_combo:hover { background: rgba(255,255,255,0.10); }
QComboBox.group_combo::drop-down { border: none; }
QComboBox QAbstractItemView {
    background: #1a1d26;
    border: 1px solid rgba(255,255,255,0.12);
    color: #c8ccd8;
    selection-background-color: #3d5afe;
}

/* ── Scroll area ── */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(255,255,255,0.15);
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.3); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* ── Status bar ── */
QStatusBar {
    background: rgba(0,0,0,0.3);
    color: rgba(255,255,255,0.35);
    font-size: 11px;
    border-top: 1px solid rgba(255,255,255,0.06);
}

/* ── Dividers ── */
QFrame#h_divider {
    background: rgba(255,255,255,0.07);
    max-height: 1px;
}

/* ── Section header ── */
QLabel.section_header {
    color: rgba(255,255,255,0.25);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
}

/* ── Dialogs ── */
QDialog {
    background: #12151e;
}
QDialog QLabel { color: #c8ccd8; }
QInputDialog QLineEdit {
    background: rgba(255,255,255,0.06);
    border: 1.5px solid rgba(255,255,255,0.12);
    border-radius: 8px;
    color: #e8eaf0;
    padding: 8px;
}
QDialogButtonBox QPushButton {
    background: rgba(61,90,254,0.8);
    border: none;
    border-radius: 8px;
    color: #ffffff;
    font-weight: 600;
    padding: 7px 18px;
    min-width: 80px;
}
QDialogButtonBox QPushButton:hover { background: #3d5afe; }
QDialogButtonBox QPushButton[text="Cancel"], QDialogButtonBox QPushButton[text="No"] {
    background: rgba(255,255,255,0.06);
    color: #c8ccd8;
}
"""

GROUP_COLORS = {
    "Work":          "#3d5afe",
    "Study":         "#00e5ff",
    "Entertainment": "#ff4081",
    "Other":         "#78909c",
    "All":           "#ffffff",
}


# ── Window Card widget ────────────────────────────────────────────────────────

class WindowCard(QFrame):
    focus_requested   = pyqtSignal(object)
    minimize_requested = pyqtSignal(object)
    close_requested   = pyqtSignal(object)
    group_changed     = pyqtSignal(object, str)

    def __init__(self, win: WindowInfo, parent=None):
        super().__init__(parent)
        self.win = win
        self.setObjectName("win_card")
        self.setProperty("class", "win_card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        # Emoji
        emoji_lbl = QLabel(self.win.emoji)
        emoji_lbl.setProperty("class", "win_emoji")
        emoji_lbl.setFixedWidth(32)
        emoji_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(emoji_lbl)

        # Text column
        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        title_text = self.win.title
        if len(title_text) > 70:
            title_text = title_text[:67] + "…"
        title_lbl = QLabel(title_text)
        title_lbl.setProperty("class", "win_title")
        title_lbl.setToolTip(self.win.title)

        proc_lbl = QLabel(self.win.process_name)
        proc_lbl.setProperty("class", "win_proc")

        text_col.addWidget(title_lbl)
        text_col.addWidget(proc_lbl)
        layout.addLayout(text_col, stretch=1)

        # Group dropdown
        group_combo = QComboBox()
        group_combo.setProperty("class", "group_combo")
        for g in GROUPS:
            group_combo.addItem(g)
        idx = GROUPS.index(self.win.group) if self.win.group in GROUPS else 3
        group_combo.setCurrentIndex(idx)
        color = GROUP_COLORS.get(self.win.group, "#78909c")
        group_combo.setStyleSheet(f"QComboBox.group_combo {{ color: {color}; }}")
        group_combo.currentTextChanged.connect(self._on_group_changed)
        layout.addWidget(group_combo)
        self._group_combo = group_combo

        # Action buttons
        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)

        focus_btn = QPushButton("Focus")
        focus_btn.setProperty("class", "card_btn")
        focus_btn.clicked.connect(lambda: self.focus_requested.emit(self.win))

        min_btn = QPushButton("Min")
        min_btn.setProperty("class", "card_btn")
        min_btn.clicked.connect(lambda: self.minimize_requested.emit(self.win))

        close_btn = QPushButton("✕")
        close_btn.setProperty("class", "card_btn")
        close_btn.setObjectName("close_btn")
        close_btn.clicked.connect(lambda: self.close_requested.emit(self.win))

        btn_col.addWidget(focus_btn)
        btn_col.addWidget(min_btn)
        btn_col.addWidget(close_btn)
        layout.addLayout(btn_col)

        # Left accent bar — group color
        self._update_accent()

    def _on_group_changed(self, group: str):
        self.win.group = group
        color = GROUP_COLORS.get(group, "#78909c")
        self._group_combo.setStyleSheet(f"QComboBox.group_combo {{ color: {color}; }}")
        self.group_changed.emit(self.win, group)
        self._update_accent()

    def _update_accent(self):
        color = GROUP_COLORS.get(self.win.group, "#78909c")
        self.setStyleSheet(
            f"QFrame.win_card {{ border-left: 3px solid {color}; }}"
        )


# ── Refresh worker thread ─────────────────────────────────────────────────────

class RefreshWorker(QThread):
    refreshed = pyqtSignal(list)

    def __init__(self, wm: WindowManager):
        super().__init__()
        self._wm = wm
        self._running = True

    def run(self):
        while self._running:
            windows = self._wm.get_windows()
            self.refreshed.emit(windows)
            self.msleep(CONFIG["refresh_interval_ms"])

    def stop(self):
        self._running = False
        self.quit()
        self.wait()


# ── Main Window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WorkspaceAI")
        self.resize(1100, 720)
        self.setMinimumSize(800, 560)

        self._wm      = WindowManager()
        self._sm      = SessionManager(CONFIG.get("sessions_dir", "sessions"))
        self._ai      = AIEngine(CONFIG.get("embedding_model", "all-MiniLM-L6-v2"))
        self._voice   = VoiceProcessor(
            backend=CONFIG.get("voice_backend", "vosk"),
            model_path=CONFIG.get("vosk_model_path", ""),
            whisper_model=CONFIG.get("whisper_model", "tiny"),
        )

        self._all_windows: List[WindowInfo] = []
        self._active_group: str = "All"
        self._search_query: str = ""
        self._listening: bool = False

        self.setStyleSheet(STYLESHEET)
        self._build_ui()
        self._start_refresh()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_divider())
        root.addWidget(self._build_group_tabs())
        root.addWidget(self._build_divider())
        root.addWidget(self._build_scroll_area(), stretch=1)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Scanning windows…")

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(72)
        header.setStyleSheet("background: rgba(0,0,0,0.2);")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(12)

        # App title
        title = QLabel("⚡ WorkspaceAI")
        title.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 700; letter-spacing: 0.5px;")
        layout.addWidget(title)

        # Search bar
        self._search_bar = QLineEdit()
        self._search_bar.setObjectName("search_bar")
        self._search_bar.setPlaceholderText("Search or type a command…")
        self._search_bar.textChanged.connect(self._on_search_changed)
        self._search_bar.returnPressed.connect(self._on_command_entered)
        layout.addWidget(self._search_bar, stretch=1)

        # Voice button
        self._voice_btn = QPushButton("🎤")
        self._voice_btn.setObjectName("voice_btn")
        self._voice_btn.setToolTip("Voice command (click to speak)")
        self._voice_btn.clicked.connect(self._on_voice_clicked)
        layout.addWidget(self._voice_btn)

        # Auto-group
        auto_btn = QPushButton("🧠 Auto-Group All")
        auto_btn.setProperty("class", "toolbar_btn")
        auto_btn.clicked.connect(self._on_auto_group)
        layout.addWidget(auto_btn)

        # Sessions menu
        session_btn = QPushButton("💾 Sessions")
        session_btn.setProperty("class", "toolbar_btn")
        session_btn.clicked.connect(self._show_sessions_menu)
        self._session_btn = session_btn
        layout.addWidget(session_btn)

        return header

    def _build_group_tabs(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(44)
        bar.setStyleSheet("background: rgba(0,0,0,0.12);")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 0, 0)
        layout.setSpacing(0)

        self._group_tabs: dict[str, QPushButton] = {}
        for group in ["All"] + GROUPS:
            btn = QPushButton(group)
            btn.setProperty("class", "group_tab")
            btn.setCheckable(False)
            btn.clicked.connect(lambda checked, g=group: self._switch_group(g))
            self._group_tabs[group] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Window count label
        self._count_label = QLabel("0 windows")
        self._count_label.setStyleSheet("color: rgba(255,255,255,0.30); font-size: 12px; padding-right: 20px;")
        layout.addWidget(self._count_label)

        self._set_active_tab("All")
        return bar

    def _build_scroll_area(self) -> QScrollArea:
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(16, 12, 16, 16)
        self._cards_layout.setSpacing(6)
        self._cards_layout.addStretch()

        self._scroll.setWidget(self._cards_container)
        return self._scroll

    def _build_divider(self) -> QFrame:
        d = QFrame()
        d.setObjectName("h_divider")
        d.setFrameShape(QFrame.Shape.HLine)
        d.setFixedHeight(1)
        return d

    # ── Refresh loop ──────────────────────────────────────────────────────────

    def _start_refresh(self):
        self._worker = RefreshWorker(self._wm)
        self._worker.refreshed.connect(self._on_windows_refreshed)
        self._worker.start()

    def _on_windows_refreshed(self, windows: List[WindowInfo]):
        self._all_windows = windows
        self._ai.update_index(windows)
        self._render_cards()

        demo_suffix = " [demo mode]" if self._wm.is_demo else ""
        self._status.showMessage(
            f"{len(windows)} windows detected{demo_suffix}  •  "
            f"Search: {'semantic' if self._ai._model else 'TF-IDF'}  •  "
            f"Voice: {'ready' if self._voice.is_available else 'unavailable'}"
        )

    # ── Card rendering ────────────────────────────────────────────────────────

    def _filtered_windows(self) -> List[WindowInfo]:
        if self._search_query:
            results = self._ai.search(self._search_query, top_k=20)
            windows = [w for w, score in results]
        else:
            windows = self._all_windows

        if self._active_group != "All":
            windows = [w for w in windows if w.group == self._active_group]

        return windows

    def _render_cards(self):
        # Remove old cards
        while self._cards_layout.count() > 1:  # keep trailing stretch
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        windows = self._filtered_windows()
        self._count_label.setText(f"{len(windows)} window{'s' if len(windows) != 1 else ''}")

        if not windows:
            empty = QLabel("No windows match your search.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: rgba(255,255,255,0.2); font-size: 14px; padding: 40px;")
            self._cards_layout.insertWidget(0, empty)
            return

        for i, win in enumerate(windows):
            card = WindowCard(win)
            card.focus_requested.connect(self._on_focus)
            card.minimize_requested.connect(self._on_minimize)
            card.close_requested.connect(self._on_close)
            card.group_changed.connect(self._on_group_changed)
            self._cards_layout.insertWidget(i, card)

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_search_changed(self, text: str):
        self._search_query = text.strip()
        self._render_cards()

    def _on_command_entered(self):
        text = self._search_bar.text().strip()
        if not text:
            return
        intent, arg = self._ai.parse_intent(text)
        self._execute_intent(intent, arg)

    def _execute_intent(self, intent: str, arg: str):
        logger.info("Intent: %s | arg: %s", intent, arg)

        if intent == "search":
            self._search_query = arg
            self._search_bar.setText(arg)
            self._render_cards()

        elif intent == "focus":
            results = self._ai.search(arg, top_k=1)
            if results:
                self._on_focus(results[0][0])

        elif intent == "switch_group":
            for g in ["All"] + GROUPS:
                if g.lower() in arg.lower():
                    self._switch_group(g)
                    break

        elif intent == "close":
            results = self._ai.search(arg, top_k=1)
            if results:
                self._on_close(results[0][0])

        elif intent == "minimize":
            results = self._ai.search(arg, top_k=1)
            if results:
                self._on_minimize(results[0][0])

        elif intent == "save_session":
            self._save_session(arg)

        elif intent == "load_session":
            self._load_session(arg)

        elif intent == "auto_group":
            self._on_auto_group()

    def _on_focus(self, win: WindowInfo):
        self._wm.focus_window(win)
        self._status.showMessage(f"Focused: {win.title}", 3000)

    def _on_minimize(self, win: WindowInfo):
        self._wm.minimize_window(win)
        self._status.showMessage(f"Minimized: {win.title}", 3000)

    def _on_close(self, win: WindowInfo):
        if CONFIG.get("confirm_close", True):
            reply = QMessageBox.question(
                self, "Close Window",
                f"Close "{win.title}"?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._wm.close_window(win)
        self._status.showMessage(f"Closed: {win.title}", 3000)

    def _on_group_changed(self, win: WindowInfo, group: str):
        self._status.showMessage(f"Moved "{win.title}" → {group}", 2000)
        self._render_cards()

    def _switch_group(self, group: str):
        self._active_group = group
        self._set_active_tab(group)
        self._render_cards()

    def _set_active_tab(self, group: str):
        for g, btn in self._group_tabs.items():
            active = g == group
            btn.setProperty("active", "true" if active else "false")
            # Force style refresh
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            if active:
                color = GROUP_COLORS.get(g, "#ffffff")
                btn.setStyleSheet(f"QPushButton.group_tab {{ border-bottom-color: {color}; color: #ffffff; }}")
            else:
                btn.setStyleSheet("")

    def _on_auto_group(self):
        self._ai.auto_group_all(self._all_windows)
        self._render_cards()
        self._status.showMessage("Auto-grouped all windows.", 3000)

    # ── Voice ─────────────────────────────────────────────────────────────────

    def _on_voice_clicked(self):
        if not self._voice.is_available:
            text, ok = QInputDialog.getText(
                self, "Voice Command (Demo)",
                "Voice backend unavailable.\nType your command:",
            )
            if ok and text:
                self._process_voice_text(text)
            return

        if self._listening:
            return

        self._listening = True
        self._voice_btn.setProperty("listening", "true")
        self._voice_btn.style().unpolish(self._voice_btn)
        self._voice_btn.style().polish(self._voice_btn)
        self._status.showMessage("🎤 Listening…")

        self._voice.listen_async(self._on_voice_result)

    def _on_voice_result(self, text: Optional[str]):
        self._listening = False
        self._voice_btn.setProperty("listening", "false")
        self._voice_btn.style().unpolish(self._voice_btn)
        self._voice_btn.style().polish(self._voice_btn)

        if text:
            self._process_voice_text(text)
        else:
            self._status.showMessage("Voice: no input detected.", 3000)

    def _process_voice_text(self, text: str):
        self._search_bar.setText(text)
        intent, arg = self._ai.parse_intent(text)
        self._execute_intent(intent, arg)
        self._status.showMessage(f"Voice: "{text}"", 4000)

    # ── Sessions ──────────────────────────────────────────────────────────────

    def _show_sessions_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #1a1d26;
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 10px;
                padding: 6px;
                color: #c8ccd8;
            }
            QMenu::item { padding: 7px 18px; border-radius: 6px; }
            QMenu::item:selected { background: rgba(61,90,254,0.3); color: #fff; }
            QMenu::separator { height: 1px; background: rgba(255,255,255,0.08); margin: 4px 8px; }
        """)

        save_act = QAction("💾  Save current session…", self)
        save_act.triggered.connect(self._prompt_save_session)
        menu.addAction(save_act)
        menu.addSeparator()

        sessions = self._sm.list_sessions()
        if sessions:
            for name in sessions:
                act = QAction(f"📂  {name}", self)
                act.triggered.connect(lambda checked, n=name: self._load_session(n))
                menu.addAction(act)
            menu.addSeparator()
            for name in sessions:
                del_act = QAction(f"🗑  Delete "{name}"", self)
                del_act.triggered.connect(lambda checked, n=name: self._delete_session(n))
                menu.addAction(del_act)
        else:
            no_act = QAction("No saved sessions", self)
            no_act.setEnabled(False)
            menu.addAction(no_act)

        btn = self._session_btn
        menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))

    def _prompt_save_session(self):
        name, ok = QInputDialog.getText(self, "Save Session", "Session name:")
        if ok and name.strip():
            self._save_session(name.strip())

    def _save_session(self, name: str):
        if not name:
            self._prompt_save_session()
            return
        ok = self._sm.save_session(name, self._all_windows)
        if ok:
            self._status.showMessage(f"Session "{name}" saved ({len(self._all_windows)} windows).", 4000)
        else:
            self._status.showMessage("Failed to save session.", 3000)

    def _load_session(self, name: str):
        data = self._sm.load_session(name)
        if not data:
            self._status.showMessage(f"Session "{name}" not found.", 3000)
            return
        matched = self._sm.match_session_to_live(data, self._all_windows)
        self._status.showMessage(
            f"Session "{name}" restored — {len(matched)}/{len(data.get('windows', []))} windows matched.",
            5000,
        )

    def _delete_session(self, name: str):
        self._sm.delete_session(name)
        self._status.showMessage(f"Session "{name}" deleted.", 3000)

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._worker.stop()
        super().closeEvent(event)
