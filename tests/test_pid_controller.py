from __future__ import annotations

from lander_sim.control.guidance import GuidanceTarget
from lander_sim.control.pid_controller import CascadedPIDController
from lander_sim.dynamics.parameters import VehicleParameters
from lander_sim.dynamics.state import LanderState



def test_pid_controller_outputs_bounded_commands() -> None:
    vehicle = VehicleParameters()
    controller = CascadedPIDController(vehicle)
    state = LanderState(5.0, 18.0, 0.5, -0.4, 0.1, 0.0, vehicle.initial_mass)
    target = GuidanceTarget(x=0.0, z=20.0)
    command = controller.step(state, target, dt=0.02)
    assert vehicle.min_thrust <= command.target_thrust <= vehicle.max_thrust
    assert abs(command.pitch_torque) <= controller.config.omega.output_limit
