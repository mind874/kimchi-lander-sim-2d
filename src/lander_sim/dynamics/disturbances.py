from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .parameters import EnvironmentParameters, VehicleParameters
from .state import LanderState


@dataclass(slots=True, frozen=True)
class DisturbanceSample:
    wind_x: float = 0.0
    wind_z: float = 0.0
    external_force_x: float = 0.0
    external_force_z: float = 0.0
    external_torque: float = 0.0


class DisturbanceModel:
    def __init__(self, vehicle: VehicleParameters):
        self._vehicle = vehicle
        self._environment: EnvironmentParameters = vehicle.environment

    def sample(self, _time_s: float, _state: LanderState) -> DisturbanceSample:
        wind_x = self._environment.wind_velocity_x if self._vehicle.enable_wind else 0.0
        wind_z = self._environment.wind_velocity_z if self._vehicle.enable_wind else 0.0
        return DisturbanceSample(wind_x=wind_x, wind_z=wind_z)


def aerodynamic_drag(
    state: LanderState,
    vehicle: VehicleParameters,
    disturbance: DisturbanceSample,
) -> np.ndarray:
    if not vehicle.enable_drag:
        return np.zeros(2, dtype=float)

    relative_velocity = np.asarray([state.vx - disturbance.wind_x, state.vz - disturbance.wind_z], dtype=float)
    speed = float(np.linalg.norm(relative_velocity))
    linear_term = -vehicle.environment.linear_drag_coefficient * relative_velocity
    quadratic_term = -vehicle.environment.quadratic_drag_coefficient * speed * relative_velocity
    return linear_term + quadratic_term
