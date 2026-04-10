from __future__ import annotations

from PySide6.QtWidgets import QListWidget, QPushButton, QVBoxLayout, QWidget

from lander_sim.simulation.history import RunResult
from lander_sim.simulation.scenarios import RuntimeConfig
from lander_sim.ui.widgets import LabeledGroup, make_combo


class PresetsPanel(QWidget):
    def __init__(self, presets: list[RuntimeConfig], parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        group = LabeledGroup('Presets and comparison')
        layout.addWidget(group)
        self.preset_combo = make_combo([preset.preset_name for preset in presets], presets[0].preset_name if presets else '')
        self.load_button = QPushButton('Load preset')
        self.save_button = QPushButton('Save config…')
        self.load_config_button = QPushButton('Load config…')
        self.run_list = QListWidget()
        self.run_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        group.form.addRow('Preset', self.preset_combo)
        group.form.addRow(self.load_button)
        group.form.addRow(self.save_button)
        group.form.addRow(self.load_config_button)
        group.form.addRow('Compare runs', self.run_list)
        layout.addStretch(1)

    def set_runs(self, runs: list[RunResult]) -> None:
        selected = {item.text() for item in self.run_list.selectedItems()}
        self.run_list.clear()
        for run in runs:
            self.run_list.addItem(f'{run.run_name} [{run.controller_mode}]')
        for index in range(self.run_list.count()):
            item = self.run_list.item(index)
            item.setSelected(item.text() in selected)
