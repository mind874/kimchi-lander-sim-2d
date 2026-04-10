from __future__ import annotations

import math

import numpy as np

from .disturbances import DisturbanceModel, DisturbanceSample, aerodynamic_drag
from .integrators import euler_step, rk4_step
from .parameters import VehicleParameters
from .state import ActuatorCommand, DerivativeResult, LanderState, PlantForces


class VehicleModel:
    def __init__(self, vehicle: VehicleParameters):
        self.vehicle = vehicle
        self.disturbance_model = DisturbanceModel(vehicle)

    @staticmethod
    def thrust_direction_world(theta: float, gimbal_angle: float = 0.0) -> np.ndarray:
        total_angle = theta + gimbal_angle
        return np.asarray([math.sin(total_angle), math.cos(total_angle)], dtype=float)

    def gimbal_torque(self, thrust: float, gimbal_angle: float) -> float:
        return self.vehicle.lever_arm * thrust * math.sin(gimbal_angle)

    @staticmethod
    def rcs_torque(rcs_command: float) -> float:
        return rcs_command

    def forces_and_moment(
        self,
        state: LanderState,
        command: ActuatorCommand,
        disturbance: DisturbanceSample | None = None,
    ) -> PlantForces:
        resolved_disturbance = disturbance or self.disturbance_model.sample(0.0, state)
        thrust_direction = self.thrust_direction_world(state.theta, command.gimbal_angle)
        thrust_world = command.thrust * thrust_direction
        drag_world = aerodynamic_drag(state, self.vehicle, resolved_disturbance)
        torque = (
            self.gimbal_torque(command.thrust, command.gimbal_angle)
            + self.rcs_torque(command.rcs_torque)
            + resolved_disturbance.external_torque
        )
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
        forces = self.forces_and_moment(state, command, resolved_disturbance)
        mass = max(state.m, self.vehicle.dry_mass)
        inertia = self.vehicle.inertia(mass)
        gravity = self.vehicle.environment.gravity

        mdot = 0.0
        if self.vehicle.enable_mass_depletion and mass > self.vehicle.dry_mass and command.thrust > 0.0:
            mdot = -command.thrust / (self.vehicle.specific_impulse * gravity)

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
    ) -> tuple[LanderState, list[dict[str, float | str]]]:
        events: list[dict[str, float | str]] = []
        state = candidate_state

        if state.m < self.vehicle.dry_mass:
            state = state.with_updates(m=self.vehicle.dry_mass)
            events.append({"time": time_s, "kind": "mass_clamped", "value": self.vehicle.dry_mass})

        ground = self.vehicle.touchdown.ground_height
        if state.z <= ground:
            touchdown_speed = abs(min(previous_state.vz, state.vz))
            horizontal_speed = abs(state.vx)
            tilt = abs(state.theta)
            crashed = (
                touchdown_speed > self.vehicle.touchdown.max_vertical_speed
                or horizontal_speed > self.vehicle.touchdown.max_horizontal_speed
                or tilt > self.vehicle.touchdown.max_tilt_rad
            )
            events.append(
                {
                    "time": time_s,
                    "kind": "crash" if crashed else "touchdown",
                    "value": touchdown_speed,
                }
            )
            state = state.with_updates(
                z=ground,
                vz=0.0,
                vx=0.0 if crashed else 0.25 * state.vx,
                omega=0.0 if crashed else 0.25 * state.omega,
            )
        return state, events

    def propagate(
        self,
        state: LanderState,
        command: ActuatorCommand,
        dt: float,
        time_s: float = 0.0,
        integrator: str = "rk4",
    ) -> tuple[LanderState, list[dict[str, float | str]]]:
        state_vector = state.as_vector()
        stepper = rk4_step if integrator == "rk4" else euler_step
        next_state_vector = stepper(
            lambda t, y: self.derivative_vector(t, y, command),
            time_s,
            state_vector,
            dt,
        )
        next_state = LanderState.from_vector(next_state_vector)
        return self.apply_state_constraints(state, next_state, time_s + dt)
