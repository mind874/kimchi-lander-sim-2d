from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def apply_dark_theme(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor('#10141c'))
    palette.setColor(QPalette.ColorRole.WindowText, QColor('#e6edf7'))
    palette.setColor(QPalette.ColorRole.Base, QColor('#0b1016'))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor('#131b24'))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor('#1c2530'))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor('#e6edf7'))
    palette.setColor(QPalette.ColorRole.Text, QColor('#d7dfeb'))
    palette.setColor(QPalette.ColorRole.Button, QColor('#17212b'))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor('#e6edf7'))
    palette.setColor(QPalette.ColorRole.Highlight, QColor('#4aa3ff'))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor('#0b1016'))
    app.setPalette(palette)
    app.setStyleSheet(
        '''
        QWidget { font-family: Inter, "SF Pro Text", Helvetica, Arial, sans-serif; font-size: 12px; }
        QMainWindow, QMenuBar, QMenu, QToolBar, QStatusBar { background: #10141c; color: #e6edf7; }
        QGroupBox { border: 1px solid #263341; border-radius: 8px; margin-top: 10px; padding-top: 12px; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #7ec4ff; }
        QTabWidget::pane, QPlainTextEdit, QListWidget, QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
            background: #0b1016; color: #d7dfeb; border: 1px solid #263341; border-radius: 6px;
        }
        QPushButton { background: #1b2936; color: #e6edf7; border: 1px solid #304457; padding: 6px 12px; border-radius: 6px; }
        QPushButton:hover { background: #213244; }
        QHeaderView::section { background: #17212b; color: #d7dfeb; border: none; padding: 4px; }
        '''
    )
