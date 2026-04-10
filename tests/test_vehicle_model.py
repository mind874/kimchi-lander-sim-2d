from __future__ import annotations

import math

from lander_sim.dynamics.parameters import VehicleParameters
from lander_sim.dynamics.state import ActuatorCommand, LanderState
from lander_sim.dynamics.vehicle_model import VehicleModel


def test_gravity_only_reduces_vertical_velocity() -> None:
    vehicle = VehicleParameters(enable_mass_depletion=False)
    model = VehicleModel(vehicle)
    state = LanderState(0.0, 20.0, 0.0, 0.0, 0.0, 0.0, vehicle.initial_mass)
    next_state, events, _ = model.propagate(state, ActuatorCommand(thrust=0.0), dt=0.1)
    assert next_state.vz < state.vz
    assert next_state.z < state.z
    assert events == []


def test_thrust_direction_matches_body_pitch() -> None:
    direction = VehicleModel.thrust_vector_body(100.0, 0.0)
    assert direction[0] == 0.0
    assert direction[1] == 100.0

    world = VehicleModel.body_to_world(math.radians(10.0), direction)
    assert world[0] > 0.0
    assert world[1] > 0.0


def test_touchdown_clamps_ground_and_records_crash() -> None:
    vehicle = VehicleParameters(enable_mass_depletion=False)
    model = VehicleModel(vehicle)
    state = LanderState(0.0, 0.1, 0.0, -5.0, 0.0, 0.0, vehicle.initial_mass)
    next_state, events, _ = model.propagate(state, ActuatorCommand(thrust=0.0), dt=0.1)
    assert next_state.z == 0.0
    assert next_state.vz == 0.0
    assert any(event['name'] == 'crash' for event in events)
