from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QLabel, QWidget


class LabeledGroup(QGroupBox):
    def __init__(self, title: str, parent: QWidget | None = None):
        super().__init__(title, parent)
        self.form = QFormLayout(self)
        self.form.setContentsMargins(10, 12, 10, 10)
        self.form.setSpacing(8)


def make_float_spin(value: float, minimum: float, maximum: float, decimals: int = 3, step: float = 0.1) -> QDoubleSpinBox:
    widget = QDoubleSpinBox()
    widget.setRange(minimum, maximum)
    widget.setDecimals(decimals)
    widget.setSingleStep(step)
    widget.setValue(value)
    return widget


def make_checkbox(value: bool) -> QCheckBox:
    widget = QCheckBox()
    widget.setChecked(value)
    return widget


def make_combo(items: list[str], current: str) -> QComboBox:
    widget = QComboBox()
    widget.addItems(items)
    index = max(widget.findText(current), 0)
    widget.setCurrentIndex(index)
    return widget


def add_hint(form: QFormLayout, text: str) -> None:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet('color: #8ea7bf; font-size: 11px;')
    form.addRow(label)
