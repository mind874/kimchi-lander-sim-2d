from __future__ import annotations

from dataclasses import dataclass, field
import math


@dataclass(slots=True, frozen=True)
class ActuatorLimits:
    min_throttle: float = 0.0
    max_throttle: float = 1.0
    max_gimbal_angle_rad: float = math.radians(12.0)
    max_rcs_torque: float = 1_800.0


@dataclass(slots=True, frozen=True)
class EnvironmentParameters:
    gravity: float = 9.80665
    air_density: float = 1.225
    wind_velocity_x: float = 0.0
    wind_velocity_z: float = 0.0
    linear_drag_coefficient: float = 0.0
    quadratic_drag_coefficient: float = 0.0


@dataclass(slots=True, frozen=True)
class EngineLagParameters:
    enabled: bool = False
    time_constant: float = 0.15


@dataclass(slots=True, frozen=True)
class TouchdownParameters:
    max_vertical_speed: float = 2.0
    max_horizontal_speed: float = 1.0
    max_tilt_rad: float = math.radians(12.0)
    ground_height: float = 0.0


@dataclass(slots=True, frozen=True)
class VehicleParameters:
    dry_mass: float = 1_200.0
    propellant_mass: float = 400.0
    nominal_mass: float = 1_600.0
    dry_inertia: float = 2_200.0
    propellant_inertia_scale: float = 2.5
    lever_arm: float = 2.8
    max_thrust: float = 30_000.0
    min_thrust: float = 0.0
    specific_impulse: float = 290.0
    body_radius: float = 1.2
    enable_mass_depletion: bool = True
    enable_variable_inertia: bool = True
    enable_drag: bool = False
    enable_wind: bool = False
    actuator_limits: ActuatorLimits = field(default_factory=ActuatorLimits)
    engine_lag: EngineLagParameters = field(default_factory=EngineLagParameters)
    environment: EnvironmentParameters = field(default_factory=EnvironmentParameters)
    touchdown: TouchdownParameters = field(default_factory=TouchdownParameters)

    @property
    def wet_mass(self) -> float:
        return self.dry_mass + self.propellant_mass

    @property
    def initial_mass(self) -> float:
        return max(self.nominal_mass, self.dry_mass)

    def inertia(self, mass: float | None = None) -> float:
        if not self.enable_variable_inertia:
            return self.dry_inertia
        resolved_mass = self.initial_mass if mass is None else max(mass, self.dry_mass)
        propellant_above_dry = max(resolved_mass - self.dry_mass, 0.0)
        return self.dry_inertia + propellant_above_dry * self.propellant_inertia_scale

    def hover_thrust(self, mass: float | None = None) -> float:
        resolved_mass = self.initial_mass if mass is None else max(mass, self.dry_mass)
        return resolved_mass * self.environment.gravity

    def throttle_to_thrust(self, throttle: float) -> float:
        clamped_throttle = min(max(throttle, self.actuator_limits.min_throttle), self.actuator_limits.max_throttle)
        return self.min_thrust + clamped_throttle * (self.max_thrust - self.min_thrust)

    def thrust_to_throttle(self, thrust: float) -> float:
        span = self.max_thrust - self.min_thrust
        if span <= 0.0:
            return self.actuator_limits.min_throttle
        throttle = (thrust - self.min_thrust) / span
        return min(max(throttle, self.actuator_limits.min_throttle), self.actuator_limits.max_throttle)
