from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout

from lander_sim.simulation.history import RunResult
from lander_sim.ui.plotting.comparison_plot_widget import ComparisonPlotWidget


class PlotManager(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.position_plot = ComparisonPlotWidget('Position', 'm')
        self.velocity_plot = ComparisonPlotWidget('Velocity', 'm/s')
        self.attitude_plot = ComparisonPlotWidget('Attitude / Mass', 'rad / kg')
        self.command_plot = ComparisonPlotWidget('Command', 'command')
        for widget in (self.position_plot, self.velocity_plot, self.attitude_plot, self.command_plot):
            layout.addWidget(widget)

    def set_results(self, current: RunResult | None, comparisons: list[RunResult]) -> None:
        for widget in (self.position_plot, self.velocity_plot, self.attitude_plot, self.command_plot):
            widget.plot.clear()
            widget.plot.addLegend(offset=(10, 10))
        if current is not None:
            self._add_result(current, primary=True)
        for result in comparisons:
            self._add_result(result, primary=False)

    def _add_result(self, result: RunResult, primary: bool) -> None:
        time = result.state_history['time']
        suffix = f"{result.preset_name}:{result.controller_mode}"
        width = 2 if primary else 1
        self.position_plot.plot.plot(time, result.state_history['x'], pen={'color': '#4aa3ff', 'width': width}, name=f'x {suffix}')
        self.position_plot.plot.plot(time, result.state_history['z'], pen={'color': '#7ec4ff', 'width': width}, name=f'z {suffix}')
        self.velocity_plot.plot.plot(time, result.state_history['vx'], pen={'color': '#f6c560', 'width': width}, name=f'vx {suffix}')
        self.velocity_plot.plot.plot(time, result.state_history['vz'], pen={'color': '#ff8a4c', 'width': width}, name=f'vz {suffix}')
        self.attitude_plot.plot.plot(time, result.state_history['theta'], pen={'color': '#d18cff', 'width': width}, name=f'theta {suffix}')
        self.attitude_plot.plot.plot(time, result.state_history['mass'], pen={'color': '#4ad295', 'width': width}, name=f'mass {suffix}')
        self.command_plot.plot.plot(time, result.command_history['throttle'], pen={'color': '#7ec4ff', 'width': width}, name=f'throttle {suffix}')
        self.command_plot.plot.plot(time, result.command_history['gimbal'], pen={'color': '#ffb266', 'width': width}, name=f'gimbal {suffix}')
        self.command_plot.plot.plot(time, result.command_history['rcs_pitch'], pen={'color': '#f76d9b', 'width': width}, name=f'rcs {suffix}')
