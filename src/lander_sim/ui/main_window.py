from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from lander_sim.simulation.history import RunResult
from lander_sim.simulation.runner import SimulationRunner
from lander_sim.simulation.scenarios import RuntimeConfig, default_runtime_config, load_preset_configs
from lander_sim.ui.panels import AnalyticsPanel, GuidancePanel, PIDPanel, PresetsPanel, SimulationPanel, StateSpacePanel, VehiclePanel
from lander_sim.ui.playback_controller import PlaybackController
from lander_sim.ui.plotting.plot_manager import PlotManager
from lander_sim.ui.scene_renderer import SceneRenderer
from lander_sim.utils.config_io import load_runtime_config, save_runtime_config


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('Kimchi Lander Sim 2D')
        self.resize(1680, 980)
        self.presets = load_preset_configs()
        self.current_config = self.presets[0] if self.presets else default_runtime_config()
        self.current_result: RunResult | None = None
        self.saved_runs: list[RunResult] = []
        self.playback = PlaybackController(self)
        self.playback.sample_changed.connect(self._on_sample_changed)
        self.playback.finished.connect(lambda: self.statusBar().showMessage('Playback finished'))

        self._build_ui()
        self._load_config_into_panels(self.current_config)
        self._refresh_state_space_display()

    def _build_ui(self) -> None:
        toolbar = QToolBar('Simulation')
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        self.run_button = QPushButton('Run')
        self.pause_button = QPushButton('Pause')
        self.reset_button = QPushButton('Reset')
        self.step_button = QPushButton('Step')
        self.controller_mode_combo = QComboBox()
        self.controller_mode_combo.addItems(['pid', 'state_space', 'open_loop'])
        self.controller_mode_combo.setCurrentText(self.current_config.controller_mode)
        for button in (self.run_button, self.pause_button, self.reset_button, self.step_button):
            toolbar.addWidget(button)
        toolbar.addSeparator()
        toolbar.addWidget(self.controller_mode_combo)
        self.run_button.clicked.connect(self.run_simulation)
        self.pause_button.clicked.connect(self._toggle_pause)
        self.reset_button.clicked.connect(self._reset_playback)
        self.step_button.clicked.connect(self.playback.step_once)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage('Ready')

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        self.tabs = QTabWidget()
        splitter.addWidget(self.tabs)

        self.vehicle_panel = VehiclePanel(self.current_config.vehicle)
        self.sim_panel = SimulationPanel(self.current_config.simulation, self.current_config.initial_state)
        self.pid_panel = PIDPanel(self.current_config.pid)
        self.state_space_panel = StateSpacePanel(self.current_config.state_space, self.current_config.vehicle, self.current_config.simulation.dt_s, self.current_config.allocator_mode)
        self.guidance_panel = GuidancePanel(self.current_config.mission)
        self.presets_panel = PresetsPanel(self.presets)
        self.analytics_panel = AnalyticsPanel()
        self.presets_panel.load_button.clicked.connect(self._load_selected_preset)
        self.presets_panel.save_button.clicked.connect(self._save_config_dialog)
        self.presets_panel.load_config_button.clicked.connect(self._load_config_dialog)
        self.presets_panel.run_list.itemSelectionChanged.connect(self._update_plot_comparison)

        self.tabs.addTab(self.vehicle_panel, 'Vehicle')
        self.tabs.addTab(self.sim_panel, 'Simulation')
        self.tabs.addTab(self.pid_panel, 'PID')
        self.tabs.addTab(self.state_space_panel, 'State-space')
        self.tabs.addTab(self.guidance_panel, 'Guidance')
        self.tabs.addTab(self.presets_panel, 'Presets')

        middle = QWidget()
        middle_layout = QVBoxLayout(middle)
        self.scene_renderer = SceneRenderer()
        middle_layout.addWidget(self.scene_renderer)
        splitter.addWidget(middle)

        right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.plot_manager = PlotManager()
        right_splitter.addWidget(self.plot_manager)
        right_splitter.addWidget(self.analytics_panel)
        splitter.addWidget(right_splitter)
        splitter.setSizes([340, 540, 800])

    def _build_runtime_config(self) -> RuntimeConfig:
        vehicle = self.vehicle_panel.apply(self.current_config.vehicle)
        simulation = self.sim_panel.simulation_settings()
        initial_state = self.sim_panel.initial_state(self.vehicle_panel.initial_mass_value())
        mission = self.guidance_panel.mission(simulation.duration_s)
        pid = self.pid_panel.config(self.current_config.pid)
        state_space = self.state_space_panel.config()
        allocator_mode = self.state_space_panel.allocator_mode.currentText()
        controller_mode = self.controller_mode_combo.currentText()
        return RuntimeConfig(
            preset_name=self.current_config.preset_name,
            description=self.current_config.description,
            controller_mode=controller_mode,
            allocator_mode=allocator_mode,
            simulation=simulation,
            vehicle=vehicle,
            initial_state=initial_state,
            mission=mission,
            pid=pid,
            state_space=state_space,
            open_loop=self.current_config.open_loop,
        )

    def _load_config_into_panels(self, config: RuntimeConfig) -> None:
        self.current_config = config
        self.controller_mode_combo.setCurrentText(config.controller_mode)
        self.vehicle_panel = VehiclePanel(config.vehicle)
        self.sim_panel = SimulationPanel(config.simulation, config.initial_state)
        self.pid_panel = PIDPanel(config.pid)
        self.state_space_panel = StateSpacePanel(config.state_space, config.vehicle, config.simulation.dt_s, config.allocator_mode)
        self.guidance_panel = GuidancePanel(config.mission)
        replacements = [self.vehicle_panel, self.sim_panel, self.pid_panel, self.state_space_panel, self.guidance_panel]
        for idx, widget in enumerate(replacements):
            current = self.tabs.widget(idx)
            self.tabs.removeTab(idx)
            current.deleteLater()
            self.tabs.insertTab(idx, widget, ['Vehicle', 'Simulation', 'PID', 'State-space', 'Guidance'][idx])
        self.tabs.setCurrentIndex(0)

    def _load_selected_preset(self) -> None:
        name = self.presets_panel.preset_combo.currentText()
        for preset in self.presets:
            if preset.preset_name == name:
                self._load_config_into_panels(preset)
                self.status.showMessage(f'Loaded preset {name}')
                self._refresh_state_space_display()
                return

    def _save_config_dialog(self) -> None:
        path_str, _ = QFileDialog.getSaveFileName(self, 'Save config', str(Path.cwd() / 'lander-config.json'), 'JSON (*.json)')
        if not path_str:
            return
        config = self._build_runtime_config()
        save_runtime_config(config, path_str)
        self.status.showMessage(f'Saved config to {path_str}')

    def _load_config_dialog(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(self, 'Load config', str(Path.cwd()), 'JSON (*.json)')
        if not path_str:
            return
        config = load_runtime_config(path_str)
        self._load_config_into_panels(config)
        self.status.showMessage(f'Loaded config from {path_str}')
        self._refresh_state_space_display()

    def run_simulation(self) -> None:
        config = self._build_runtime_config()
        self.current_config = config
        self._refresh_state_space_display()
        try:
            result = SimulationRunner(config).run()
        except Exception as exc:  # pragma: no cover - interactive path
            QMessageBox.critical(self, 'Simulation failed', str(exc))
            return
        result.metadata['vehicle_length_m'] = config.vehicle.vehicle_length_m
        result.metadata['allocator_mode'] = config.allocator_mode
        self.current_result = result
        self.saved_runs.append(result)
        self.presets_panel.set_runs(self.saved_runs)
        self.plot_manager.set_results(result, self._comparison_runs())
        self.analytics_panel.set_result(result)
        self.playback.set_result(result, config.simulation.dt_s, config.simulation.playback_speed)
        self.playback.play()
        self.status.showMessage(f'Completed simulation for {config.preset_name} ({config.controller_mode})')

    def _comparison_runs(self) -> list[RunResult]:
        selected = {item.text() for item in self.presets_panel.run_list.selectedItems()}
        return [run for run in self.saved_runs if f'{run.run_name} [{run.controller_mode}]' in selected and run is not self.current_result]

    def _update_plot_comparison(self) -> None:
        self.plot_manager.set_results(self.current_result, self._comparison_runs())

    def _on_sample_changed(self, index: int) -> None:
        self.scene_renderer.update_view(self.current_result, index)
        if self.current_result and self.current_result.samples:
            sample = self.current_result.samples[index]
            self.status.showMessage(
                f't={sample.time_s:5.2f}s | mode={self.current_result.controller_mode} | x={sample.state.x:6.2f} m z={sample.state.z:6.2f} m | sat={sample.saturated}'
            )

    def _refresh_state_space_display(self) -> None:
        self.state_space_panel.refresh_display(
            self._build_runtime_config().vehicle,
            self.sim_panel.dt_s.value(),
            self.state_space_panel.config(),
        )

    def _toggle_pause(self) -> None:
        if self.pause_button.text() == 'Pause':
            self.playback.pause()
            self.pause_button.setText('Resume')
            self.status.showMessage('Playback paused')
        else:
            self.playback.play()
            self.pause_button.setText('Pause')

    def _reset_playback(self) -> None:
        self.playback.reset()
        self.pause_button.setText('Pause')
        self.scene_renderer.update_view(self.current_result, 0)
        self.status.showMessage('Playback reset')
