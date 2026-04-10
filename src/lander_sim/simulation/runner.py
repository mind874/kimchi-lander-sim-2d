from __future__ import annotations

from dataclasses import dataclass
import math

from lander_sim.control.actuator_allocator import ActuatorAllocator
from lander_sim.control.guidance import GuidanceTarget
from lander_sim.control.pid_controller import CascadedPIDController
from lander_sim.control.state_space_controller import StateSpaceController
from lander_sim.dynamics.state import AbstractControlCommand, ActuatorCommand, LanderState
from lander_sim.dynamics.vehicle_model import VehicleModel
from lander_sim.simulation.analytics import compute_run_analytics
from lander_sim.simulation.history import RunResult, SimulationSample
from lander_sim.simulation.scenarios import RuntimeConfig


@dataclass(slots=True)
class ActuatorRuntime:
    thrust_n: float = 0.0
    gimbal_rad: float = 0.0


class SimulationRunner:
    def __init__(self, config: RuntimeConfig):
        self.config = config
        self.vehicle_model = VehicleModel(config.vehicle)
        self.allocator = ActuatorAllocator(config.vehicle, mode=config.allocator_mode)
        self.pid_controller = CascadedPIDController(config.vehicle, config.pid)
        self.state_space_controller = StateSpaceController(config.vehicle, config.simulation.dt_s, config.state_space)
        self.actuator_runtime = ActuatorRuntime(thrust_n=config.vehicle.hover_thrust(config.initial_state.m))

    def run(self) -> RunResult:
        result = RunResult(
            run_name=f"{self.config.preset_name}-{self.config.controller_mode}",
            preset_name=self.config.preset_name,
            controller_mode=self.config.controller_mode,
            allocator_mode=self.config.allocator_mode,
            metadata={
                "target": {
                    "x_m": self.config.mission.sample(self.config.simulation.duration_s).x,
                    "z_m": self.config.mission.sample(self.config.simulation.duration_s).z,
                },
                "actuator_limits": {
                    "throttle_max": self.config.vehicle.actuator_limits.max_throttle,
                    "gimbal_limit_rad": self.config.vehicle.actuator_limits.max_gimbal_angle_rad,
                    "rcs_torque_limit_nm": self.config.vehicle.actuator_limits.max_rcs_torque,
                },
                "allocator_mode": self.config.allocator_mode,
            },
        )
        state = self.config.initial_state
        dt = self.config.simulation.dt_s
        total_steps = max(1, int(self.config.simulation.duration_s / dt))
        self.pid_controller.reset()

        for step in range(total_steps + 1):
            time_s = step * dt
            target = self.config.mission.sample(time_s)
            abstract_command = self._compute_abstract_command(state, target, dt)
            allocation = self.allocator.allocate(abstract_command)
            command = self._apply_actuator_dynamics(allocation.command, dt)
            next_state, events, forces = self.vehicle_model.propagate(
                state=state,
                command=command,
                dt=dt,
                time_s=time_s,
                integrator=self.config.simulation.integrator,
            )
            result.append(
                SimulationSample(
                    time_s=time_s,
                    state=state,
                    target=target,
                    abstract_command=abstract_command,
                    actuator_command=command,
                    forces=forces,
                    saturated=allocation.saturated,
                    events=tuple(events),
                )
            )
            state = next_state
            if any(event["name"] in {"touchdown", "crash"} for event in events):
                break

        result.analytics = compute_run_analytics(result.to_analytics_input())
        return result

    def _compute_abstract_command(self, state: LanderState, target: GuidanceTarget, dt: float) -> AbstractControlCommand:
        if self.config.controller_mode == "state_space":
            return self.state_space_controller.step(state, target)
        if self.config.controller_mode == "open_loop":
            thrust = self.config.vehicle.throttle_to_thrust(self.config.open_loop.throttle)
            requested_gimbal = math.radians(self.config.open_loop.gimbal_deg)
            pitch_torque = thrust * self.config.vehicle.lever_arm * math.sin(requested_gimbal) + self.config.open_loop.rcs_torque_n_m
            return AbstractControlCommand(
                target_thrust=thrust,
                pitch_torque=pitch_torque,
                source="open_loop",
                debug={"delta_thrust": thrust - self.config.vehicle.hover_thrust(state.m), "requested_gimbal_deg": self.config.open_loop.gimbal_deg},
            )
        return self.pid_controller.step(state, target, dt)

    def _apply_actuator_dynamics(self, command: ActuatorCommand, dt: float) -> ActuatorCommand:
        target_thrust = self.config.vehicle.clamp_thrust(command.thrust)
        if self.config.vehicle.enable_engine_lag and self.config.vehicle.engine_lag.time_constant_s > 1e-6:
            alpha = dt / (self.config.vehicle.engine_lag.time_constant_s + dt)
            self.actuator_runtime.thrust_n += alpha * (target_thrust - self.actuator_runtime.thrust_n)
        else:
            self.actuator_runtime.thrust_n = target_thrust

        rate_limit = self.config.vehicle.actuator_limits.gimbal_rate_limit_rad_s
        delta = command.gimbal_angle - self.actuator_runtime.gimbal_rad
        max_delta = rate_limit * dt
        delta = max(min(delta, max_delta), -max_delta)
        self.actuator_runtime.gimbal_rad += delta

        throttle = self.config.vehicle.thrust_to_throttle(self.actuator_runtime.thrust_n)
        return ActuatorCommand(
            thrust=self.actuator_runtime.thrust_n,
            gimbal_angle=self.actuator_runtime.gimbal_rad,
            rcs_torque=max(min(command.rcs_torque, self.config.vehicle.actuator_limits.max_rcs_torque), -self.config.vehicle.actuator_limits.max_rcs_torque),
            metadata={**command.metadata, "throttle": throttle},
        )
