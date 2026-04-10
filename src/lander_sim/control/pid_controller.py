from __future__ import annotations

from dataclasses import dataclass, field
import math

from lander_sim.control.guidance import GuidanceTarget
from lander_sim.dynamics.parameters import VehicleParameters
from lander_sim.dynamics.state import AbstractControlCommand, LanderState


@dataclass(slots=True, frozen=True)
class PIDAxisGains:
    kp: float
    ki: float = 0.0
    kd: float = 0.0
    integrator_limit: float = math.inf
    output_limit: float = math.inf
    derivative_filter_tau: float = 0.05
    anti_windup_gain: float = 1.0


@dataclass(slots=True, frozen=True)
class PIDAxisTerms:
    proportional: float
    integral: float
    derivative: float
    output: float


@dataclass(slots=True, frozen=True)
class PIDAxisSnapshot:
    error: float
    measured_derivative: float
    filtered_derivative: float
    terms: PIDAxisTerms


class PIDAxisController:
    def __init__(self, gains: PIDAxisGains):
        self.gains = gains
        self.integral = 0.0
        self.previous_measurement: float | None = None
        self.filtered_derivative = 0.0

    def reset(self) -> None:
        self.integral = 0.0
        self.previous_measurement = None
        self.filtered_derivative = 0.0

    def step(
        self,
        setpoint: float,
        measurement: float,
        dt: float,
        feedforward: float = 0.0,
        measurement_rate: float | None = None,
    ) -> tuple[float, PIDAxisSnapshot]:
        if dt <= 0.0:
            raise ValueError("PID step requires dt > 0")

        raw_rate = 0.0
        if measurement_rate is not None:
            raw_rate = measurement_rate
        elif self.previous_measurement is not None:
            raw_rate = (measurement - self.previous_measurement) / dt

        if math.isfinite(self.gains.derivative_filter_tau) and self.gains.derivative_filter_tau > 0.0:
            alpha = dt / (self.gains.derivative_filter_tau + dt)
        else:
            alpha = 1.0
        self.filtered_derivative = (1.0 - alpha) * self.filtered_derivative + alpha * raw_rate

        error = setpoint - measurement
        proportional = self.gains.kp * error
        derivative = -self.gains.kd * self.filtered_derivative
        raw_output = proportional + self.integral + derivative + feedforward
        limited_output = min(max(raw_output, -self.gains.output_limit), self.gains.output_limit)

        self.integral += self.gains.ki * error * dt + self.gains.anti_windup_gain * (limited_output - raw_output) * dt
        self.integral = min(max(self.integral, -self.gains.integrator_limit), self.gains.integrator_limit)

        output = min(max(proportional + self.integral + derivative + feedforward, -self.gains.output_limit), self.gains.output_limit)
        self.previous_measurement = measurement
        return output, PIDAxisSnapshot(
            error=error,
            measured_derivative=raw_rate,
            filtered_derivative=self.filtered_derivative,
            terms=PIDAxisTerms(
                proportional=proportional,
                integral=self.integral,
                derivative=derivative,
                output=output,
            ),
        )


@dataclass(slots=True, frozen=True)
class CascadedPIDConfig:
    x_position: PIDAxisGains = field(default_factory=lambda: PIDAxisGains(0.20, ki=0.00, kd=0.05, output_limit=4.0))
    x_velocity: PIDAxisGains = field(default_factory=lambda: PIDAxisGains(0.35, ki=0.02, kd=0.08, output_limit=math.radians(15.0)))
    z_position: PIDAxisGains = field(default_factory=lambda: PIDAxisGains(0.35, ki=0.02, kd=0.10, output_limit=3.0))
    z_velocity: PIDAxisGains = field(default_factory=lambda: PIDAxisGains(6.0, ki=1.2, kd=2.5, integrator_limit=8.0, output_limit=8.0))
    theta: PIDAxisGains = field(default_factory=lambda: PIDAxisGains(5.5, ki=0.2, kd=0.8, output_limit=4.0))
    omega: PIDAxisGains = field(default_factory=lambda: PIDAxisGains(900.0, ki=45.0, kd=180.0, integrator_limit=1_000.0, output_limit=6_000.0))
    max_theta_command_rad: float = math.radians(15.0)
    max_vertical_speed_command: float = 4.0
    max_lateral_speed_command: float = 4.0


class CascadedPIDController:
    def __init__(self, vehicle: VehicleParameters, config: CascadedPIDConfig | None = None):
        self.vehicle = vehicle
        self.config = config or CascadedPIDConfig()
        self.x_position = PIDAxisController(self.config.x_position)
        self.x_velocity = PIDAxisController(self.config.x_velocity)
        self.z_position = PIDAxisController(self.config.z_position)
        self.z_velocity = PIDAxisController(self.config.z_velocity)
        self.theta = PIDAxisController(self.config.theta)
        self.omega = PIDAxisController(self.config.omega)

    def reset(self) -> None:
        for axis in (self.x_position, self.x_velocity, self.z_position, self.z_velocity, self.theta, self.omega):
            axis.reset()

    def step(self, state: LanderState, target: GuidanceTarget, dt: float) -> AbstractControlCommand:
        lateral_speed_cmd, x_pos_snapshot = self.x_position.step(target.x, state.x, dt, feedforward=target.vx)
        lateral_speed_cmd = min(max(lateral_speed_cmd, -self.config.max_lateral_speed_command), self.config.max_lateral_speed_command)

        theta_cmd, x_vel_snapshot = self.x_velocity.step(lateral_speed_cmd, state.vx, dt, measurement_rate=0.0)
        theta_cmd = min(max(theta_cmd + target.theta, -self.config.max_theta_command_rad), self.config.max_theta_command_rad)

        vertical_speed_cmd, z_pos_snapshot = self.z_position.step(target.z, state.z, dt, feedforward=target.vz)
        vertical_speed_cmd = min(max(vertical_speed_cmd, -self.config.max_vertical_speed_command), self.config.max_vertical_speed_command)

        vertical_accel_cmd, z_vel_snapshot = self.z_velocity.step(vertical_speed_cmd, state.vz, dt, measurement_rate=0.0)
        target_thrust = state.m * (self.vehicle.environment.gravity + vertical_accel_cmd)
        target_thrust = min(max(target_thrust, self.vehicle.min_thrust), self.vehicle.max_thrust)

        omega_cmd, theta_snapshot = self.theta.step(theta_cmd, state.theta, dt, feedforward=target.omega)
        pitch_torque, omega_snapshot = self.omega.step(omega_cmd, state.omega, dt, measurement_rate=0.0)

        debug = {
            "theta_cmd": theta_cmd,
            "vertical_speed_cmd": vertical_speed_cmd,
            "lateral_speed_cmd": lateral_speed_cmd,
            "x_position_error": x_pos_snapshot.error,
            "x_velocity_error": x_vel_snapshot.error,
            "z_position_error": z_pos_snapshot.error,
            "z_velocity_error": z_vel_snapshot.error,
            "theta_error": theta_snapshot.error,
            "omega_error": omega_snapshot.error,
            "thrust_output": target_thrust,
            "torque_output": pitch_torque,
        }
        return AbstractControlCommand(target_thrust=target_thrust, pitch_torque=pitch_torque, source="pid", debug=debug)
