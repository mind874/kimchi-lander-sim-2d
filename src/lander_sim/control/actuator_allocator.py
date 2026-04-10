from __future__ import annotations

from dataclasses import dataclass
import math

from lander_sim.dynamics.parameters import VehicleParameters
from lander_sim.dynamics.state import AbstractControlCommand, ActuatorCommand


@dataclass(slots=True, frozen=True)
class ActuatorAllocation:
    command: ActuatorCommand
    achieved_torque: float
    saturated: bool
    mode: str


class ActuatorAllocator:
    def __init__(self, vehicle: VehicleParameters, mode: str = "hybrid"):
        self.vehicle = vehicle
        self.mode = mode

    def allocate(self, request: AbstractControlCommand) -> ActuatorAllocation:
        thrust = min(max(request.target_thrust, self.vehicle.min_thrust), self.vehicle.max_thrust)
        saturated = not math.isclose(thrust, request.target_thrust, rel_tol=1e-9, abs_tol=1e-9)
        target_torque = request.pitch_torque
        achieved_torque = 0.0
        gimbal_angle = 0.0
        rcs_torque = 0.0

        max_gimbal_torque = self.vehicle.lever_arm * max(thrust, 0.0) * math.sin(self.vehicle.actuator_limits.max_gimbal_angle_rad)

        if self.mode == "gimbal_only":
            achieved_torque = min(max(target_torque, -max_gimbal_torque), max_gimbal_torque)
            saturated = saturated or not math.isclose(achieved_torque, target_torque, rel_tol=1e-9, abs_tol=1e-9)
            if thrust > 1e-6 and self.vehicle.lever_arm > 0.0:
                ratio = achieved_torque / (self.vehicle.lever_arm * thrust)
                gimbal_angle = math.asin(min(max(ratio, -1.0), 1.0))
        elif self.mode == "rcs_only":
            rcs_torque = min(max(target_torque, -self.vehicle.actuator_limits.max_rcs_torque), self.vehicle.actuator_limits.max_rcs_torque)
            achieved_torque = rcs_torque
            saturated = saturated or not math.isclose(achieved_torque, target_torque, rel_tol=1e-9, abs_tol=1e-9)
        else:
            gimbal_component = min(max(target_torque, -max_gimbal_torque), max_gimbal_torque)
            remaining = target_torque - gimbal_component
            rcs_torque = min(max(remaining, -self.vehicle.actuator_limits.max_rcs_torque), self.vehicle.actuator_limits.max_rcs_torque)
            achieved_torque = gimbal_component + rcs_torque
            saturated = saturated or not math.isclose(achieved_torque, target_torque, rel_tol=1e-9, abs_tol=1e-9)
            if thrust > 1e-6 and self.vehicle.lever_arm > 0.0:
                ratio = gimbal_component / (self.vehicle.lever_arm * thrust)
                gimbal_angle = math.asin(min(max(ratio, -1.0), 1.0))

        return ActuatorAllocation(
            command=ActuatorCommand(
                thrust=thrust,
                gimbal_angle=gimbal_angle,
                rcs_torque=rcs_torque,
                metadata={
                    "source": request.source,
                    "requested_torque": target_torque,
                },
            ),
            achieved_torque=achieved_torque,
            saturated=saturated,
            mode=self.mode,
        )
