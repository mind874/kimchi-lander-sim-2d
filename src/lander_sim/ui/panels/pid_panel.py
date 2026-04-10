from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from lander_sim.control.pid_controller import CascadedPIDConfig, PIDAxisGains
from lander_sim.ui.widgets import LabeledGroup, add_hint, make_float_spin


class PIDPanel(QWidget):
    def __init__(self, config: CascadedPIDConfig, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.alt_kp = make_float_spin(config.z_velocity.kp, 0.0, 20.0, step=0.1)
        self.alt_ki = make_float_spin(config.z_velocity.ki, 0.0, 10.0, step=0.05)
        self.alt_kd = make_float_spin(config.z_velocity.kd, 0.0, 10.0, step=0.1)
        self.lat_kp = make_float_spin(config.x_velocity.kp, 0.0, 10.0, step=0.05)
        self.lat_ki = make_float_spin(config.x_velocity.ki, 0.0, 5.0, step=0.05)
        self.lat_kd = make_float_spin(config.x_velocity.kd, 0.0, 5.0, step=0.05)
        self.att_kp = make_float_spin(config.theta.kp, 0.0, 20.0, step=0.1)
        self.att_ki = make_float_spin(config.theta.ki, 0.0, 5.0, step=0.05)
        self.att_kd = make_float_spin(config.theta.kd, 0.0, 10.0, step=0.1)
        group = LabeledGroup('Cascaded PID gains')
        layout.addWidget(group)
        for label, widget in (
            ('Altitude Kp', self.alt_kp), ('Altitude Ki', self.alt_ki), ('Altitude Kd', self.alt_kd),
            ('Lateral Kp', self.lat_kp), ('Lateral Ki', self.lat_ki), ('Lateral Kd', self.lat_kd),
            ('Attitude Kp', self.att_kp), ('Attitude Ki', self.att_ki), ('Attitude Kd', self.att_kd),
        ):
            group.form.addRow(label, widget)
        add_hint(group.form, 'Outer position loops shape velocity targets; inner loops command attitude and thrust.')
        layout.addStretch(1)

    def config(self, base: CascadedPIDConfig) -> CascadedPIDConfig:
        return CascadedPIDConfig(
            x_position=base.x_position,
            x_velocity=PIDAxisGains(self.lat_kp.value(), self.lat_ki.value(), self.lat_kd.value(), output_limit=base.x_velocity.output_limit),
            z_position=base.z_position,
            z_velocity=PIDAxisGains(self.alt_kp.value(), self.alt_ki.value(), self.alt_kd.value(), integrator_limit=base.z_velocity.integrator_limit, output_limit=base.z_velocity.output_limit),
            theta=PIDAxisGains(self.att_kp.value(), self.att_ki.value(), self.att_kd.value(), output_limit=base.theta.output_limit),
            omega=base.omega,
            max_theta_command_rad=base.max_theta_command_rad,
            max_vertical_speed_command=base.max_vertical_speed_command,
            max_lateral_speed_command=base.max_lateral_speed_command,
        )
