from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QBrush, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsPolygonItem, QGraphicsScene, QGraphicsTextItem, QGraphicsView

from lander_sim.simulation.history import RunResult


class SceneRenderer(QGraphicsView):
    def __init__(self, parent=None):
        self.scene = QGraphicsScene()
        super().__init__(self.scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setBackgroundBrush(QColor('#0b1016'))
        self.setSceneRect(QRectF(-80, -10, 160, 120))
        self.scale(1, -1)
        self._trail_item = None
        self._body_item = QGraphicsPolygonItem()
        self._body_item.setBrush(QBrush(QColor('#d8e7ff')))
        self._body_item.setPen(QPen(QColor('#96bbff'), 0))
        self.scene.addItem(self._body_item)
        self._thrust_item = QGraphicsLineItem()
        self._thrust_item.setPen(QPen(QColor('#ff8a4c'), 0))
        self.scene.addItem(self._thrust_item)
        self._velocity_item = QGraphicsLineItem()
        self._velocity_item.setPen(QPen(QColor('#4ad295'), 0))
        self.scene.addItem(self._velocity_item)
        self._target_item = QGraphicsPolygonItem()
        self._target_item.setBrush(QBrush(QColor('#4aa3ff')))
        self._target_item.setPen(QPen(QColor('#4aa3ff'), 0))
        self.scene.addItem(self._target_item)
        self._label = QGraphicsTextItem()
        self._label.setDefaultTextColor(QColor('#d7dfeb'))
        self._label.setScale(0.15)
        self._label.setPos(-78, 105)
        self._label.setTransform(self._label.transform().scale(1, -1))
        self.scene.addItem(self._label)
        self._ground = self.scene.addLine(-100, 0, 100, 0, QPen(QColor('#7ec4ff'), 0))

    def update_view(self, result: RunResult | None, index: int) -> None:
        if result is None or not result.samples:
            return
        index = max(0, min(index, len(result.samples) - 1))
        sample = result.samples[index]
        scale = 0.5 * result.metadata.get('vehicle_length_m', 5.5)
        x = sample.state.x
        z = sample.state.z
        theta = sample.state.theta

        body = [
            QPointF(x + scale * 0.18, z - scale),
            QPointF(x - scale * 0.18, z - scale),
            QPointF(x - scale * 0.32, z + scale * 0.7),
            QPointF(x, z + scale),
            QPointF(x + scale * 0.32, z + scale * 0.7),
        ]
        polygon = QPolygonF(body)
        transform = polygon
        self._body_item.setPolygon(transform)
        self._body_item.setRotation(-theta * 180.0 / 3.141592653589793)
        self._body_item.setTransformOriginPoint(QPointF(x, z))

        thrust_scale = sample.actuator_command.thrust / 2500.0
        self._thrust_item.setLine(x, z - scale, x - thrust_scale * 0.35 * (sample.forces.thrust_world_x), z - scale - thrust_scale * 0.35 * (sample.forces.thrust_world_z))
        self._velocity_item.setLine(x, z, x + sample.state.vx * 1.8, z + sample.state.vz * 1.8)

        target = sample.target
        self._target_item.setPolygon(QPolygonF([
            QPointF(target.x - 0.8, target.z),
            QPointF(target.x, target.z + 0.8),
            QPointF(target.x + 0.8, target.z),
            QPointF(target.x, target.z - 0.8),
        ]))

        trail = QPolygonF([QPointF(s.state.x, s.state.z) for s in result.samples[: index + 1]])
        if self._trail_item is not None:
            self.scene.removeItem(self._trail_item)
        self._trail_item = self.scene.addPolygon(trail, QPen(QColor('#4aa3ff'), 0))
        self._label.setPlainText(
            f"t={sample.time_s:5.2f}s  x={sample.state.x:6.2f}m  z={sample.state.z:6.2f}m  theta={sample.state.theta * 57.2958:5.2f}deg"
        )
