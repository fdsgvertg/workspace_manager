"""
WorkspaceAI — Main Entry Point
Wires all modules together and launches the application.
"""

import sys
import os
import logging
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# Setup logging
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("main")


def main():
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont

    app = QApplication(sys.argv)
    app.setApplicationName("WorkspaceAI")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("WorkspaceAI")

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    logger.info("WorkspaceAI started.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
