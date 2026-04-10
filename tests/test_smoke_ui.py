from __future__ import annotations

from PySide6.QtWidgets import QApplication

from lander_sim.ui.main_window import MainWindow



def test_main_window_smoke() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert window.vehicle_panel is not None
    assert window.sim_panel is not None
    assert window.plot_manager is not None
    assert window.analytics_panel is not None
    assert window.statusBar() is not None
    window.close()
