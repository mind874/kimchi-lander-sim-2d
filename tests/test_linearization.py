from __future__ import annotations

import math
import numpy as np

from lander_sim.dynamics.linearization import continuous_hover_linearization, hover_trim
from lander_sim.dynamics.parameters import VehicleParameters



def test_hover_trim_matches_weight() -> None:
    vehicle = VehicleParameters()
    state, trim_input = hover_trim(vehicle)
    assert math.isclose(trim_input[0], state.m * vehicle.environment.gravity, rel_tol=1e-9)


def test_discrete_matrices_have_expected_shape() -> None:
    linearization = continuous_hover_linearization(VehicleParameters(), dt=0.02)
    assert linearization.A.shape == (6, 6)
    assert linearization.B.shape == (6, 2)
    assert linearization.Ad.shape == (6, 6)
    assert linearization.Bd.shape == (6, 2)
    assert np.isfinite(linearization.Ad).all()
    assert np.isfinite(linearization.Bd).all()
