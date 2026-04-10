from __future__ import annotations

import math

from PySide6.QtWidgets import QVBoxLayout, QWidget

from lander_sim.dynamics.parameters import ActuatorLimits, VehicleParameters
from lander_sim.ui.widgets import LabeledGroup, add_hint, make_checkbox, make_float_spin


class VehiclePanel(QWidget):
    def __init__(self, vehicle: VehicleParameters, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        group = LabeledGroup('Vehicle')
        layout.addWidget(group)
        self.dry_mass = make_float_spin(vehicle.dry_mass, 100.0, 5000.0, step=10.0)
        self.initial_mass = make_float_spin(vehicle.initial_mass, 100.0, 5000.0, step=10.0)
        self.inertia = make_float_spin(vehicle.nominal_inertia, 100.0, 10000.0, step=10.0)
        self.max_thrust = make_float_spin(vehicle.max_thrust, 1000.0, 100000.0, step=100.0)
        self.min_thrust = make_float_spin(vehicle.min_thrust, 0.0, 50000.0, step=100.0)
        self.gimbal_limit_deg = make_float_spin(math.degrees(vehicle.actuator_limits.max_gimbal_angle_rad), 0.0, 45.0, step=0.5)
        self.gimbal_rate_deg_s = make_float_spin(math.degrees(vehicle.actuator_limits.gimbal_rate_limit_rad_s), 1.0, 360.0, step=1.0)
        self.rcs_limit = make_float_spin(vehicle.actuator_limits.max_rcs_torque, 0.0, 10000.0, step=50.0)
        self.enable_mass = make_checkbox(vehicle.enable_mass_depletion)
        self.enable_inertia = make_checkbox(vehicle.enable_variable_inertia)
        self.enable_drag = make_checkbox(vehicle.enable_drag)
        self.enable_wind = make_checkbox(vehicle.enable_wind)
        self.enable_engine_lag = make_checkbox(vehicle.enable_engine_lag)
        for label, widget in (
            ('Dry mass [kg]', self.dry_mass),
            ('Initial mass [kg]', self.initial_mass),
            ('Iyy [kg m²]', self.inertia),
            ('Max thrust [N]', self.max_thrust),
            ('Min thrust [N]', self.min_thrust),
            ('Gimbal limit [deg]', self.gimbal_limit_deg),
            ('Gimbal rate [deg/s]', self.gimbal_rate_deg_s),
            ('RCS torque limit [N m]', self.rcs_limit),
            ('Mass depletion', self.enable_mass),
            ('Variable inertia', self.enable_inertia),
            ('Drag enabled', self.enable_drag),
            ('Wind enabled', self.enable_wind),
            ('Engine lag', self.enable_engine_lag),
        ):
            group.form.addRow(label, widget)
        add_hint(group.form, 'Shared plant parameters used by both PID and state-space controllers.')
        layout.addStretch(1)

    def apply(self, vehicle: VehicleParameters) -> VehicleParameters:
        initial_mass = max(self.initial_mass.value(), self.dry_mass.value())
        return VehicleParameters(
            dry_mass=self.dry_mass.value(),
            propellant_mass=max(initial_mass - self.dry_mass.value(), 0.0),
            dry_inertia=self.inertia.value(),
            nominal_inertia=self.inertia.value(),
            lever_arm=vehicle.lever_arm,
            vehicle_length_m=vehicle.vehicle_length_m,
            vehicle_radius_m=vehicle.vehicle_radius_m,
            thrust_line_offset_m=vehicle.thrust_line_offset_m,
            nominal_cg_offset_m=vehicle.nominal_cg_offset_m,
            cg_shift_per_propellant_m=vehicle.cg_shift_per_propellant_m,
            specific_impulse=vehicle.specific_impulse,
            min_thrust=self.min_thrust.value(),
            max_thrust=self.max_thrust.value(),
            enable_mass_depletion=self.enable_mass.isChecked(),
            enable_variable_inertia=self.enable_inertia.isChecked(),
            enable_drag=self.enable_drag.isChecked(),
            enable_wind=self.enable_wind.isChecked(),
            enable_engine_lag=self.enable_engine_lag.isChecked(),
            enable_cg_shift=vehicle.enable_cg_shift,
            actuator_limits=ActuatorLimits(
                min_throttle=vehicle.actuator_limits.min_throttle,
                max_throttle=vehicle.actuator_limits.max_throttle,
                max_gimbal_angle_rad=math.radians(self.gimbal_limit_deg.value()),
                gimbal_rate_limit_rad_s=math.radians(self.gimbal_rate_deg_s.value()),
                max_rcs_torque=self.rcs_limit.value(),
            ),
            engine_lag=vehicle.engine_lag,
            environment=vehicle.environment,
            touchdown=vehicle.touchdown,
        )

    def initial_mass_value(self) -> float:
        return max(self.initial_mass.value(), self.dry_mass.value())
