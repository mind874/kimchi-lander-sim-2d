from __future__ import annotations

from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget

from lander_sim.simulation.history import RunResult


class AnalyticsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.view = QPlainTextEdit()
        self.view.setReadOnly(True)
        layout.addWidget(self.view)

    def set_result(self, result: RunResult | None) -> None:
        if result is None or result.analytics is None:
            self.view.setPlainText('Run analytics will appear here after simulation.')
            return
        analytics = result.analytics
        self.view.setPlainText(
            '\n'.join(
                [
                    f'Run: {analytics.run_name}',
                    f'Preset: {analytics.preset_name}',
                    f'Controller: {analytics.controller_mode}',
                    f'Final position error: {analytics.final_position_error_m:.3f} m',
                    f'Touchdown velocity: {analytics.touchdown_velocity_mps if analytics.touchdown_velocity_mps is not None else float("nan"):.3f} m/s',
                    f'Peak angle: {analytics.peak_angle_deg:.3f} deg',
                    f'Fuel consumed: {analytics.fuel_consumed_kg:.3f} kg',
                    f'RCS pulse count: {analytics.rcs_pulse_count}',
                    f'Saturation fraction: {analytics.saturation_fraction:.3f}',
                    f'Landing pass: {analytics.landing_pass}',
                    f'Events: {", ".join(analytics.event_flags) or "none"}',
                ]
            )
        )
