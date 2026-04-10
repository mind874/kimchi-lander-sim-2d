from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


@dataclass(slots=True, frozen=True)
class GuidanceTarget:
    x: float
    z: float
    vx: float = 0.0
    vz: float = 0.0
    theta: float = 0.0
    omega: float = 0.0
    label: str = "hold"

    def as_vector(self) -> npt.NDArray[np.float64]:
        return np.asarray([self.x, self.z, self.vx, self.vz, self.theta, self.omega], dtype=float)


@dataclass(slots=True, frozen=True)
class GuidanceSegment:
    start_time: float
    end_time: float
    target: GuidanceTarget

    def contains(self, time_s: float) -> bool:
        return self.start_time <= time_s < self.end_time


@dataclass(slots=True, frozen=True)
class MissionProfile:
    name: str
    segments: tuple[GuidanceSegment, ...]

    def sample(self, time_s: float) -> GuidanceTarget:
        if not self.segments:
            raise ValueError("Mission profile requires at least one segment")
        for segment in self.segments:
            if segment.contains(time_s):
                return segment.target
        return self.segments[-1].target


def make_hover_profile(altitude_m: float = 20.0, duration_s: float = 10.0, x_target_m: float = 0.0) -> MissionProfile:
    return MissionProfile(
        name="stable_hover",
        segments=(
            GuidanceSegment(0.0, duration_s, GuidanceTarget(x=x_target_m, z=altitude_m, label="hover")),
        ),
    )


def make_lateral_translation_profile(
    altitude_m: float = 20.0,
    start_x_m: float = 0.0,
    target_x_m: float = 8.0,
    hold_time_s: float = 2.0,
    translate_time_s: float = 4.0,
    settle_time_s: float = 4.0,
) -> MissionProfile:
    lateral_rate = (target_x_m - start_x_m) / max(translate_time_s, 1e-6)
    return MissionProfile(
        name="lateral_translation",
        segments=(
            GuidanceSegment(0.0, hold_time_s, GuidanceTarget(x=start_x_m, z=altitude_m, label="hold_start")),
            GuidanceSegment(
                hold_time_s,
                hold_time_s + translate_time_s,
                GuidanceTarget(x=target_x_m, z=altitude_m, vx=lateral_rate, label="translate"),
            ),
            GuidanceSegment(
                hold_time_s + translate_time_s,
                hold_time_s + translate_time_s + settle_time_s,
                GuidanceTarget(x=target_x_m, z=altitude_m, label="hold_target"),
            ),
        ),
    )


def make_hop_landing_profile(
    ascent_altitude_m: float = 20.0,
    hover_time_s: float = 2.0,
    descent_time_s: float = 6.0,
    final_x_m: float = 0.0,
) -> MissionProfile:
    descent_rate = -ascent_altitude_m / max(descent_time_s, 1e-6)
    return MissionProfile(
        name="hop_land",
        segments=(
            GuidanceSegment(0.0, hover_time_s, GuidanceTarget(x=0.0, z=ascent_altitude_m, label="hover")),
            GuidanceSegment(
                hover_time_s,
                hover_time_s + descent_time_s,
                GuidanceTarget(x=final_x_m, z=0.0, vz=descent_rate, label="descent"),
            ),
            GuidanceSegment(
                hover_time_s + descent_time_s,
                hover_time_s + descent_time_s + 1.0,
                GuidanceTarget(x=final_x_m, z=0.0, label="touchdown"),
            ),
        ),
    )
