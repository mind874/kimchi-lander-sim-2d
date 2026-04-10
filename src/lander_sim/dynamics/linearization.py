from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from scipy.linalg import expm

from .parameters import VehicleParameters
from .state import LanderState


STATE_LABELS = ("x", "z", "vx", "vz", "theta", "omega")
INPUT_LABELS = ("delta_thrust", "tau_pitch")


@dataclass(slots=True, frozen=True)
class HoverLinearization:
    A: npt.NDArray[np.float64]
    B: npt.NDArray[np.float64]
    Ad: npt.NDArray[np.float64]
    Bd: npt.NDArray[np.float64]
    trim_state: LanderState
    trim_input: npt.NDArray[np.float64]
    state_labels: tuple[str, ...] = STATE_LABELS
    input_labels: tuple[str, ...] = INPUT_LABELS


def hover_trim(vehicle: VehicleParameters, mass: float | None = None) -> tuple[LanderState, npt.NDArray[np.float64]]:
    trim_mass = vehicle.initial_mass if mass is None else max(mass, vehicle.dry_mass)
    trim_state = LanderState(x=0.0, z=0.0, vx=0.0, vz=0.0, theta=0.0, omega=0.0, m=trim_mass)
    trim_input = np.asarray([vehicle.hover_thrust(trim_mass), 0.0], dtype=float)
    return trim_state, trim_input


def discretize_linear_system(
    A: npt.NDArray[np.float64],
    B: npt.NDArray[np.float64],
    dt: float,
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    state_dim, input_dim = B.shape
    augmented = np.zeros((state_dim + input_dim, state_dim + input_dim), dtype=float)
    augmented[:state_dim, :state_dim] = A * dt
    augmented[:state_dim, state_dim:] = B * dt
    matrix_exp = expm(augmented)
    Ad = matrix_exp[:state_dim, :state_dim]
    Bd = matrix_exp[:state_dim, state_dim:]
    return Ad, Bd


def continuous_hover_linearization(
    vehicle: VehicleParameters,
    dt: float,
    mass: float | None = None,
) -> HoverLinearization:
    trim_state, trim_input = hover_trim(vehicle, mass)
    resolved_mass = trim_state.m
    inertia = vehicle.inertia(resolved_mass)
    gravity = vehicle.environment.gravity
    drag = vehicle.environment.linear_drag_coefficient if vehicle.enable_drag else 0.0

    A = np.zeros((6, 6), dtype=float)
    B = np.zeros((6, 2), dtype=float)

    A[0, 2] = 1.0
    A[1, 3] = 1.0
    A[2, 2] = -drag / resolved_mass
    A[2, 4] = gravity
    A[3, 3] = -drag / resolved_mass
    A[4, 5] = 1.0

    B[3, 0] = 1.0 / resolved_mass
    B[5, 1] = 1.0 / inertia

    Ad, Bd = discretize_linear_system(A, B, dt)
    return HoverLinearization(A=A, B=B, Ad=Ad, Bd=Bd, trim_state=trim_state, trim_input=trim_input)
