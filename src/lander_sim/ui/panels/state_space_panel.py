from __future__ import annotations

from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget

from lander_sim.control.state_space_controller import StateSpaceConfig, StateSpaceController
from lander_sim.dynamics.parameters import VehicleParameters
from lander_sim.ui.widgets import LabeledGroup, add_hint, make_combo, make_float_spin


class StateSpacePanel(QWidget):
    def __init__(self, config: StateSpaceConfig, vehicle: VehicleParameters, dt_s: float, allocator_mode: str = "hybrid", parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        config_group = LabeledGroup('State-space / LQR')
        display_group = LabeledGroup('Hover linearization')
        layout.addWidget(config_group)
        layout.addWidget(display_group)
        self.q_fields = [make_float_spin(value, 0.0, 200.0, step=0.5) for value in config.q_diagonal]
        self.r_fields = [make_float_spin(value, 0.001, 50.0, step=0.05) for value in config.r_diagonal]
        self.allocator_mode = make_combo(['hybrid', 'gimbal_only', 'rcs_only'], allocator_mode)
        for index, widget in enumerate(self.q_fields, start=1):
            config_group.form.addRow(f'Q[{index}]', widget)
        for index, widget in enumerate(self.r_fields, start=1):
            config_group.form.addRow(f'R[{index}]', widget)
        config_group.form.addRow('Allocator', self.allocator_mode)
        add_hint(config_group.form, 'The state vector is [x, z, vx, vz, theta, omega]; inputs are [delta thrust, pitch torque].')
        self.matrix_view = QPlainTextEdit()
        self.matrix_view.setReadOnly(True)
        self.matrix_view.setMinimumHeight(220)
        display_group.form.addRow(self.matrix_view)
        layout.addStretch(1)
        self.refresh_display(vehicle, dt_s, self.config())

    def config(self) -> StateSpaceConfig:
        return StateSpaceConfig(
            q_diagonal=tuple(field.value() for field in self.q_fields),
            r_diagonal=tuple(field.value() for field in self.r_fields),
        )

    def refresh_display(self, vehicle: VehicleParameters, dt_s: float, config: StateSpaceConfig) -> None:
        controller = StateSpaceController(vehicle, dt_s, config)
        self.matrix_view.setPlainText(
            '\n'.join([
                'A =', str(controller.A), '',
                'B =', str(controller.B), '',
                'K =', str(controller.K), '',
                'Poles =', str(controller.closed_loop_poles),
            ])
        )
