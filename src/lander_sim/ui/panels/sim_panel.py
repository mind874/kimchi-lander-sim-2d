from __future__ import annotations

import math

from PySide6.QtWidgets import QVBoxLayout, QWidget

from lander_sim.dynamics.state import LanderState
from lander_sim.simulation.scenarios import SimulationSettings
from lander_sim.ui.widgets import LabeledGroup, add_hint, make_combo, make_float_spin


class SimulationPanel(QWidget):
    def __init__(self, settings: SimulationSettings, initial_state: LanderState, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        sim_group = LabeledGroup('Simulation')
        init_group = LabeledGroup('Initial state')
        layout.addWidget(sim_group)
        layout.addWidget(init_group)

        self.dt_s = make_float_spin(settings.dt_s, 0.005, 0.2, decimals=3, step=0.005)
        self.duration_s = make_float_spin(settings.duration_s, 1.0, 120.0, decimals=2, step=1.0)
        self.playback_speed = make_float_spin(settings.playback_speed, 0.1, 8.0, decimals=2, step=0.1)
        self.integrator = make_combo(['rk4', 'euler'], settings.integrator)
        sim_group.form.addRow('dt [s]', self.dt_s)
        sim_group.form.addRow('Duration [s]', self.duration_s)
        sim_group.form.addRow('Playback speed', self.playback_speed)
        sim_group.form.addRow('Integrator', self.integrator)
        add_hint(sim_group.form, 'RK4 is the default integrator; Euler is available for debug/comparison.')

        self.x_m = make_float_spin(initial_state.x, -100.0, 100.0, step=0.5)
        self.z_m = make_float_spin(initial_state.z, 0.0, 200.0, step=0.5)
        self.vx = make_float_spin(initial_state.vx, -20.0, 20.0, step=0.1)
        self.vz = make_float_spin(initial_state.vz, -20.0, 20.0, step=0.1)
        self.theta_deg = make_float_spin(math.degrees(initial_state.theta), -45.0, 45.0, step=0.5)
        self.omega_deg_s = make_float_spin(math.degrees(initial_state.omega), -180.0, 180.0, step=1.0)
        for label, widget in (
            ('x [m]', self.x_m), ('z [m]', self.z_m), ('vx [m/s]', self.vx), ('vz [m/s]', self.vz), ('theta [deg]', self.theta_deg), ('omega [deg/s]', self.omega_deg_s)
        ):
            init_group.form.addRow(label, widget)
        add_hint(init_group.form, 'All simulation math runs in SI units and radians internally.')
        layout.addStretch(1)

    def simulation_settings(self) -> SimulationSettings:
        return SimulationSettings(
            dt_s=self.dt_s.value(),
            duration_s=self.duration_s.value(),
            playback_speed=self.playback_speed.value(),
            integrator=self.integrator.currentText(),
        )

    def initial_state(self, mass: float) -> LanderState:
        return LanderState(
            x=self.x_m.value(),
            z=self.z_m.value(),
            vx=self.vx.value(),
            vz=self.vz.value(),
            theta=math.radians(self.theta_deg.value()),
            omega=math.radians(self.omega_deg_s.value()),
            m=mass,
        )
