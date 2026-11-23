"""Точка входа приложения."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QApplication

from transcribo.gui.main_window import MainWindow


def vocabulary_path() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    return Path(base) / "vocabulary.json"


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Transcribo")
    app.setOrganizationName("Transcribo")

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())