from __future__ import annotations

import math

from PySide6.QtWidgets import QVBoxLayout, QWidget

from lander_sim.control.guidance import GuidanceSegment, GuidanceTarget, MissionProfile
from lander_sim.ui.widgets import LabeledGroup, add_hint, make_combo, make_float_spin


class GuidancePanel(QWidget):
    def __init__(self, mission: MissionProfile, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        group = LabeledGroup('Guidance')
        layout.addWidget(group)
        current_target = mission.sample(0.0)
        self.mode = make_combo(['hover', 'translate', 'hop'], 'hover' if mission.name == 'hover' else mission.name)
        self.target_x = make_float_spin(current_target.x, -50.0, 50.0, step=0.5)
        self.target_z = make_float_spin(current_target.z, 0.0, 100.0, step=0.5)
        self.duration_translate = make_float_spin(10.0, 1.0, 60.0, step=0.5)
        self.hover_time = make_float_spin(2.0, 0.5, 30.0, step=0.5)
        group.form.addRow('Mode', self.mode)
        group.form.addRow('Target x [m]', self.target_x)
        group.form.addRow('Target z [m]', self.target_z)
        group.form.addRow('Translate duration [s]', self.duration_translate)
        group.form.addRow('Hover/hold time [s]', self.hover_time)
        add_hint(group.form, 'Use hover for fixed-point hold, translate for lateral step, and hop for ascent-descent missions.')
        layout.addStretch(1)

    def mission(self, duration_s: float) -> MissionProfile:
        mode = self.mode.currentText()
        target = GuidanceTarget(x=self.target_x.value(), z=self.target_z.value(), theta=0.0, label=mode)
        if mode == 'translate':
            hold = self.hover_time.value()
            translate = self.duration_translate.value()
            return MissionProfile(
                name='translate',
                segments=(
                    GuidanceSegment(0.0, hold, GuidanceTarget(0.0, self.target_z.value(), label='hold_start')),
                    GuidanceSegment(hold, hold + translate, GuidanceTarget(self.target_x.value(), self.target_z.value(), label='translate')),
                    GuidanceSegment(hold + translate, duration_s, GuidanceTarget(self.target_x.value(), self.target_z.value(), label='hold_target')),
                ),
            )
        if mode == 'hop':
            hover = self.hover_time.value()
            return MissionProfile(
                name='hop',
                segments=(
                    GuidanceSegment(0.0, hover, GuidanceTarget(0.0, self.target_z.value(), label='hover')),
                    GuidanceSegment(hover, duration_s, GuidanceTarget(0.0, 0.0, vz=-max(self.target_z.value() / max(duration_s - hover, 1.0), 0.5), label='land')),
                ),
            )
        return MissionProfile(name='hover', segments=(GuidanceSegment(0.0, duration_s, target),))
