from __future__ import annotations

import numpy as np

from lander_sim.dynamics.integrators import euler_step, integrate_fixed_step, rk4_step



def test_integrators_advance_simple_ode() -> None:
    derivative = lambda _t, y: -y
    y0 = np.asarray([1.0])
    euler = euler_step(derivative, 0.0, y0, 0.1)
    rk4 = rk4_step(derivative, 0.0, y0, 0.1)
    assert euler[0] < 1.0
    assert rk4[0] < 1.0
    assert abs(rk4[0] - np.exp(-0.1)) < abs(euler[0] - np.exp(-0.1))


def test_integrate_fixed_step_history_length() -> None:
    history = integrate_fixed_step(lambda _t, y: y * 0.0 + 1.0, [0.0], dt=0.2, steps=5)
    assert len(history) == 6
