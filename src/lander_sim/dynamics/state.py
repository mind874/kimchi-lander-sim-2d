from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np
import numpy.typing as npt


StateVector = npt.NDArray[np.float64]


@dataclass(slots=True, frozen=True)
class LanderState:
    x: float
    z: float
    vx: float
    vz: float
    theta: float
    omega: float
    m: float

    def as_vector(self) -> StateVector:
        return np.asarray([self.x, self.z, self.vx, self.vz, self.theta, self.omega, self.m], dtype=float)

    @classmethod
    def from_vector(cls, vector: npt.ArrayLike) -> "LanderState":
        x, z, vx, vz, theta, omega, mass = np.asarray(vector, dtype=float)
        return cls(float(x), float(z), float(vx), float(vz), float(theta), float(omega), float(mass))

    def with_updates(self, **updates: float) -> "LanderState":
        return replace(self, **updates)


@dataclass(slots=True, frozen=True)
class ActuatorCommand:
    thrust: float
    gimbal_angle: float = 0.0
    rcs_torque: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class AbstractControlCommand:
    target_thrust: float
    pitch_torque: float
    source: str = "open_loop"
    debug: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class PlantForces:
    thrust_world_x: float
    thrust_world_z: float
    drag_world_x: float
    drag_world_z: float
    external_force_x: float
    external_force_z: float
    torque: float

    @property
    def total_force_x(self) -> float:
        return self.thrust_world_x + self.drag_world_x + self.external_force_x

    @property
    def total_force_z(self) -> float:
        return self.thrust_world_z + self.drag_world_z + self.external_force_z


@dataclass(slots=True, frozen=True)
class DerivativeResult:
    state_dot: StateVector
    forces: PlantForces
