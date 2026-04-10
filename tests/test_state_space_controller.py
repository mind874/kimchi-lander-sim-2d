from __future__ import annotations

from lander_sim.control.guidance import GuidanceTarget
from lander_sim.control.state_space_controller import StateSpaceController
from lander_sim.dynamics.parameters import VehicleParameters
from lander_sim.dynamics.state import LanderState



def test_state_space_controller_exposes_matrices_and_poles() -> None:
    vehicle = VehicleParameters()
    controller = StateSpaceController(vehicle, control_dt=0.02)
    assert controller.A.shape == (6, 6)
    assert controller.B.shape == (6, 2)
    assert controller.K.shape == (2, 6)
    assert len(controller.closed_loop_poles) == 6



def test_state_space_controller_generates_thrust_and_torque() -> None:
    vehicle = VehicleParameters()
    controller = StateSpaceController(vehicle, control_dt=0.02)
    state = LanderState(0.4, 19.5, 0.2, -0.1, 0.05, 0.0, vehicle.initial_mass)
    target = GuidanceTarget(x=0.0, z=20.0)
    command = controller.step(state, target)
    assert vehicle.min_thrust <= command.target_thrust <= vehicle.max_thrust + controller.config.max_delta_thrust
    assert abs(command.pitch_torque) <= controller.config.max_pitch_torque
