from __future__ import annotations

from collections.abc import Callable

import numpy as np
import numpy.typing as npt


StateVector = npt.NDArray[np.float64]
DerivativeFn = Callable[[float, StateVector], StateVector]


def euler_step(derivative_fn: DerivativeFn, time_s: float, state: StateVector, dt: float) -> StateVector:
    return np.asarray(state, dtype=float) + dt * derivative_fn(time_s, np.asarray(state, dtype=float))


def rk4_step(derivative_fn: DerivativeFn, time_s: float, state: StateVector, dt: float) -> StateVector:
    y = np.asarray(state, dtype=float)
    k1 = derivative_fn(time_s, y)
    k2 = derivative_fn(time_s + 0.5 * dt, y + 0.5 * dt * k1)
    k3 = derivative_fn(time_s + 0.5 * dt, y + 0.5 * dt * k2)
    k4 = derivative_fn(time_s + dt, y + dt * k3)
    return y + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def integrate_fixed_step(
    derivative_fn: DerivativeFn,
    initial_state: npt.ArrayLike,
    dt: float,
    steps: int,
    method: str = "rk4",
) -> list[StateVector]:
    stepper = rk4_step if method == "rk4" else euler_step
    state = np.asarray(initial_state, dtype=float)
    history = [state.copy()]
    time_s = 0.0
    for _ in range(steps):
        state = stepper(derivative_fn, time_s, state, dt)
        time_s += dt
        history.append(state.copy())
    return history
