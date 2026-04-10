from __future__ import annotations

from dataclasses import dataclass, field
import math


G0 = 9.80665


@dataclass(slots=True, frozen=True)
class ActuatorLimits:
    min_throttle: float = 0.0
    max_throttle: float = 1.0
    max_gimbal_angle_rad: float = math.radians(10.0)
    gimbal_rate_limit_rad_s: float = math.radians(45.0)
    max_rcs_torque: float = 1_500.0


@dataclass(slots=True, frozen=True)
class EnvironmentParameters:
    gravity: float = G0
    wind_velocity_x: float = 0.0
    wind_velocity_z: float = 0.0
    linear_drag_coefficient: float = 0.0
    quadratic_drag_coefficient: float = 0.0


@dataclass(slots=True, frozen=True)
class EngineLagParameters:
    enabled: bool = False
    time_constant_s: float = 0.15


@dataclass(slots=True, frozen=True)
class TouchdownParameters:
    max_vertical_speed: float = 2.0
    max_horizontal_speed: float = 1.0
    max_tilt_rad: float = math.radians(12.0)
    ground_height: float = 0.0
    freeze_on_crash: bool = True


@dataclass(slots=True, frozen=True)
class VehicleParameters:
    dry_mass: float = 1_200.0
    propellant_mass: float = 250.0
    dry_inertia: float = 920.0
    nominal_inertia: float = 920.0
    lever_arm: float = 2.6
    vehicle_length_m: float = 5.5
    vehicle_radius_m: float = 0.7
    thrust_line_offset_m: float = 0.0
    nominal_cg_offset_m: float = 0.0
    cg_shift_per_propellant_m: float = 0.0
    specific_impulse: float = 285.0
    min_thrust: float = 0.0
    max_thrust: float = 22_000.0
    enable_mass_depletion: bool = True
    enable_variable_inertia: bool = True
    enable_drag: bool = False
    enable_wind: bool = False
    enable_engine_lag: bool = False
    enable_cg_shift: bool = False
    actuator_limits: ActuatorLimits = field(default_factory=ActuatorLimits)
    engine_lag: EngineLagParameters = field(default_factory=EngineLagParameters)
    environment: EnvironmentParameters = field(default_factory=EnvironmentParameters)
    touchdown: TouchdownParameters = field(default_factory=TouchdownParameters)

    @property
    def wet_mass(self) -> float:
        return self.dry_mass + self.propellant_mass

    @property
    def initial_mass(self) -> float:
        return self.wet_mass

    @property
    def available_propellant_mass(self) -> float:
        return max(self.propellant_mass, 0.0)

    def mass_fraction(self, mass: float) -> float:
        if self.available_propellant_mass <= 1e-9:
            return 0.0
        return min(max((max(mass, self.dry_mass) - self.dry_mass) / self.available_propellant_mass, 0.0), 1.0)

    def inertia(self, mass: float | None = None) -> float:
        if not self.enable_variable_inertia:
            return self.nominal_inertia
        resolved_mass = self.initial_mass if mass is None else max(mass, self.dry_mass)
        propellant_ratio = self.mass_fraction(resolved_mass)
        return self.dry_inertia + propellant_ratio * max(self.nominal_inertia - self.dry_inertia, 0.0)

    def cg_offset(self, mass: float | None = None) -> float:
        resolved_mass = self.initial_mass if mass is None else max(mass, self.dry_mass)
        if not self.enable_cg_shift:
            return self.nominal_cg_offset_m
        return self.nominal_cg_offset_m + self.cg_shift_per_propellant_m * self.mass_fraction(resolved_mass)

    def hover_thrust(self, mass: float | None = None) -> float:
        resolved_mass = self.initial_mass if mass is None else max(mass, self.dry_mass)
        return resolved_mass * self.environment.gravity

    def clamp_thrust(self, thrust: float) -> float:
        return min(max(thrust, self.min_thrust), self.max_thrust)

    def thrust_to_throttle(self, thrust: float) -> float:
        span = self.max_thrust - self.min_thrust
        if span <= 1e-9:
            return self.actuator_limits.min_throttle
        throttle = (self.clamp_thrust(thrust) - self.min_thrust) / span
        return min(max(throttle, self.actuator_limits.min_throttle), self.actuator_limits.max_throttle)

    def throttle_to_thrust(self, throttle: float) -> float:
        clamped = min(max(throttle, self.actuator_limits.min_throttle), self.actuator_limits.max_throttle)
        return self.min_thrust + clamped * (self.max_thrust - self.min_thrust)

    def mass_flow_rate(self, thrust: float) -> float:
        if not self.enable_mass_depletion:
            return 0.0
        clamped_thrust = self.clamp_thrust(thrust)
        if clamped_thrust <= 0.0:
            return 0.0
        return clamped_thrust / (self.specific_impulse * G0)
