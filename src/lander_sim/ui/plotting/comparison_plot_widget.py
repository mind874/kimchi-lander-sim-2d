from __future__ import annotations

import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout


class ComparisonPlotWidget(QWidget):
    def __init__(self, title: str, y_label: str, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.plot = pg.PlotWidget(title=title)
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setLabel('left', y_label)
        self.plot.setLabel('bottom', 'Time', units='s')
        self.plot.addLegend(offset=(10, 10))
        layout.addWidget(self.plot)
