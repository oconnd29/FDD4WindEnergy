"""Launch the FDD Evaluation protocol builder."""

from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from fdd_eval.paths import app_icon_path
from fdd_eval.ui.main_window import MainWindow
from fdd_eval.ui.style import STYLE


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("FDD Evaluation")
    icon = app_icon_path()
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
