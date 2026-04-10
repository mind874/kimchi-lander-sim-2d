from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal

from lander_sim.simulation.history import RunResult


class PlaybackController(QObject):
    sample_changed = Signal(int)
    finished = Signal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._result: RunResult | None = None
        self._index = 0
        self._interval_ms = 20

    @property
    def index(self) -> int:
        return self._index

    def set_result(self, result: RunResult, dt_s: float, playback_speed: float) -> None:
        self._result = result
        self._index = 0
        speed = max(playback_speed, 0.1)
        self._interval_ms = max(int(dt_s * 1000.0 / speed), 1)
        self._timer.setInterval(self._interval_ms)
        self.sample_changed.emit(self._index)

    def play(self) -> None:
        if self._result is not None:
            self._timer.start(self._interval_ms)

    def pause(self) -> None:
        self._timer.stop()

    def reset(self) -> None:
        self.pause()
        self._index = 0
        if self._result is not None:
            self.sample_changed.emit(self._index)

    def step_once(self) -> None:
        self.pause()
        self._advance()

    def _advance(self) -> None:
        if self._result is None:
            return
        if self._index >= max(len(self._result.samples) - 1, 0):
            self.pause()
            self.finished.emit()
            return
        self._index += 1
        self.sample_changed.emit(self._index)
