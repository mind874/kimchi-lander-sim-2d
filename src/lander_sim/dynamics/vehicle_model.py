from __future__ import annotations

import math

import numpy as np

from .disturbances import DisturbanceModel, DisturbanceSample, aerodynamic_drag
from .integrators import euler_step, rk4_step
from .parameters import VehicleParameters
from .state import ActuatorCommand, DerivativeResult, LanderState, PlantForces


class VehicleModel:
    """Explicit planar rigid-body plant for the hop vehicle."""

    def __init__(self, vehicle: VehicleParameters):
        self.vehicle = vehicle
        self.disturbance_model = DisturbanceModel(vehicle)

    @staticmethod
    def body_to_world(theta: float, vector_body: np.ndarray) -> np.ndarray:
        x_body, z_body = float(vector_body[0]), float(vector_body[1])
        return np.asarray(
            [
                x_body * math.cos(theta) + z_body * math.sin(theta),
                -x_body * math.sin(theta) + z_body * math.cos(theta),
            ],
            dtype=float,
        )

    @staticmethod
    def thrust_vector_body(thrust: float, gimbal_angle: float) -> np.ndarray:
        return np.asarray(
            [
                thrust * math.sin(gimbal_angle),
                thrust * math.cos(gimbal_angle),
            ],
            dtype=float,
        )

    def engine_moment_arm_body(self, mass: float) -> np.ndarray:
        cg_offset = self.vehicle.cg_offset(mass)
        return np.asarray(
            [
                self.vehicle.thrust_line_offset_m,
                -(self.vehicle.lever_arm + cg_offset),
            ],
            dtype=float,
        )

    @staticmethod
    def planar_cross_moment(moment_arm_body: np.ndarray, force_body: np.ndarray) -> float:
        return moment_arm_body[0] * force_body[1] - moment_arm_body[1] * force_body[0]

    def forces_and_moment(
        self,
        time_s: float,
        state: LanderState,
        command: ActuatorCommand,
        disturbance: DisturbanceSample | None = None,
    ) -> PlantForces:
        resolved_disturbance = disturbance or self.disturbance_model.sample(time_s, state)
        thrust_body = self.thrust_vector_body(command.thrust, command.gimbal_angle)
        thrust_world = self.body_to_world(state.theta, thrust_body)
        drag_world = aerodynamic_drag(state, self.vehicle, resolved_disturbance)
        torque = self.planar_cross_moment(self.engine_moment_arm_body(state.m), thrust_body)
        torque += command.rcs_torque + resolved_disturbance.external_torque
        return PlantForces(
            thrust_world_x=float(thrust_world[0]),
            thrust_world_z=float(thrust_world[1]),
            drag_world_x=float(drag_world[0]),
            drag_world_z=float(drag_world[1]),
            external_force_x=resolved_disturbance.external_force_x,
            external_force_z=resolved_disturbance.external_force_z,
            torque=float(torque),
        )

    def derivatives(
        self,
        time_s: float,
        state: LanderState,
        command: ActuatorCommand,
        disturbance: DisturbanceSample | None = None,
    ) -> DerivativeResult:
        resolved_disturbance = disturbance or self.disturbance_model.sample(time_s, state)
        forces = self.forces_and_moment(time_s, state, command, resolved_disturbance)
        mass = max(state.m, self.vehicle.dry_mass)
        inertia = self.vehicle.inertia(mass)
        gravity = self.vehicle.environment.gravity
        mdot = -self.vehicle.mass_flow_rate(command.thrust)
        if mass <= self.vehicle.dry_mass + 1e-9:
            mdot = 0.0
        state_dot = np.asarray(
            [
                state.vx,
                state.vz,
                forces.total_force_x / mass,
                forces.total_force_z / mass - gravity,
                state.omega,
                forces.torque / inertia,
                mdot,
            ],
            dtype=float,
        )
        return DerivativeResult(state_dot=state_dot, forces=forces)

    def derivative_vector(self, time_s: float, state_vector: np.ndarray, command: ActuatorCommand) -> np.ndarray:
        state = LanderState.from_vector(state_vector)
        return self.derivatives(time_s, state, command).state_dot

    def apply_state_constraints(
        self,
        previous_state: LanderState,
        candidate_state: LanderState,
        time_s: float,
    ) -> tuple[LanderState, list[dict[str, float | str | bool]]]:
        events: list[dict[str, float | str | bool]] = []
        state = candidate_state

        if state.m < self.vehicle.dry_mass:
            state = state.with_updates(m=self.vehicle.dry_mass)
            events.append({"time": time_s, "name": "mass_clamped", "value": self.vehicle.dry_mass})

        ground = self.vehicle.touchdown.ground_height
        if state.z <= ground:
            touchdown_speed = math.hypot(state.vx, state.vz)
            crashed = (
                abs(state.vz) > self.vehicle.touchdown.max_vertical_speed
                or abs(state.vx) > self.vehicle.touchdown.max_horizontal_speed
                or abs(state.theta) > self.vehicle.touchdown.max_tilt_rad
            )
            event_name = "crash" if crashed else "touchdown"
            events.append(
                {
                    "time": time_s,
                    "name": event_name,
                    "touchdown_velocity_mps": touchdown_speed,
                    "hard_landing": crashed,
                }
            )
            damped_vx = 0.0 if crashed else 0.2 * previous_state.vx
            damped_omega = 0.0 if crashed else 0.2 * previous_state.omega
            state = state.with_updates(
                z=ground,
                vz=0.0,
                vx=damped_vx,
                omega=damped_omega,
            )
        return state, events

    def propagate(
        self,
        state: LanderState,
        command: ActuatorCommand,
        dt: float,
        time_s: float = 0.0,
        integrator: str = "rk4",
    ) -> tuple[LanderState, list[dict[str, float | str | bool]], PlantForces]:
        stepper = rk4_step if integrator == "rk4" else euler_step
        next_state_vector = stepper(
            lambda t, y: self.derivative_vector(t, y, command),
            time_s,
            state.as_vector(),
            dt,
        )
        next_state = LanderState.from_vector(next_state_vector)
        constrained_state, events = self.apply_state_constraints(state, next_state, time_s + dt)
        forces = self.forces_and_moment(time_s, state, command)
        return constrained_state, events, forces
