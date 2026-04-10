from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from lander_sim.ui.main_window import MainWindow
from lander_sim.ui.theme import apply_dark_theme


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName('Kimchi Lander Sim 2D')
    apply_dark_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()
