from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import math
from typing import Any

from lander_sim.control.guidance import GuidanceSegment, GuidanceTarget, MissionProfile, make_hover_profile
from lander_sim.control.pid_controller import CascadedPIDConfig, PIDAxisGains
from lander_sim.control.state_space_controller import StateSpaceConfig
from lander_sim.dynamics.parameters import ActuatorLimits, TouchdownParameters, VehicleParameters
from lander_sim.dynamics.state import LanderState

PRESET_DIR = Path(__file__).resolve().parents[1] / "data" / "presets"
PRESET_ORDER = [
    "stable_hover.json",
    "poorly_tuned_pid.json",
    "well_tuned_pid.json",
    "state_space_hover.json",
    "lateral_translation.json",
    "landing_mass_depletion.json",
    "rcs_pitch_test.json",
    "gimbal_pitch_stabilization.json",
]


@dataclass(slots=True, frozen=True)
class SimulationSettings:
    dt_s: float = 0.02
    duration_s: float = 12.0
    playback_speed: float = 1.0
    integrator: str = "rk4"


@dataclass(slots=True, frozen=True)
class OpenLoopSettings:
    throttle: float = 0.65
    gimbal_deg: float = 0.0
    rcs_torque_n_m: float = 0.0


@dataclass(slots=True)
class RuntimeConfig:
    preset_name: str = "Custom"
    description: str = "Custom configuration"
    controller_mode: str = "pid"
    allocator_mode: str = "hybrid"
    simulation: SimulationSettings = field(default_factory=SimulationSettings)
    vehicle: VehicleParameters = field(default_factory=VehicleParameters)
    initial_state: LanderState = field(default_factory=lambda: LanderState(0.0, 20.0, 0.0, 0.0, 0.0, 0.0, 1450.0))
    mission: MissionProfile = field(default_factory=make_hover_profile)
    pid: CascadedPIDConfig = field(default_factory=CascadedPIDConfig)
    state_space: StateSpaceConfig = field(default_factory=StateSpaceConfig)
    open_loop: OpenLoopSettings = field(default_factory=OpenLoopSettings)


def default_runtime_config() -> RuntimeConfig:
    return config_from_dict(json.loads((PRESET_DIR / "stable_hover.json").read_text()))


def list_preset_paths() -> list[Path]:
    discovered = {path.name: path for path in PRESET_DIR.glob("*.json")}
    ordered = [discovered[name] for name in PRESET_ORDER if name in discovered]
    remainder = sorted(path for name, path in discovered.items() if name not in PRESET_ORDER)
    return ordered + remainder


def load_preset_configs() -> list[RuntimeConfig]:
    return [config_from_dict(json.loads(path.read_text())) for path in list_preset_paths()]


def load_config(path: Path) -> RuntimeConfig:
    return config_from_dict(json.loads(path.read_text()))


def save_config(config: RuntimeConfig, path: Path) -> None:
    path.write_text(json.dumps(config_to_dict(config), indent=2))


def config_to_dict(config: RuntimeConfig) -> dict[str, Any]:
    target = config.mission.sample(config.simulation.duration_s)
    guidance_dict = {
        "mode": "sequence" if len(config.mission.segments) > 1 else "hover",
        "segments": [
            {
                "name": segment.target.label,
                "duration_s": segment.end_time - segment.start_time,
                "target": {
                    "x_m": segment.target.x,
                    "z_m": segment.target.z,
                    "vx_mps": segment.target.vx,
                    "vz_mps": segment.target.vz,
                    "theta_deg": math.degrees(segment.target.theta),
                },
            }
            for segment in config.mission.segments
        ],
    }
    return {
        "schema_version": 1,
        "preset_name": config.preset_name,
        "description": config.description,
        "controller_mode": config.controller_mode,
        "allocator_mode": config.allocator_mode,
        "simulation": asdict(config.simulation),
        "vehicle": {
            "dry_mass_kg": config.vehicle.dry_mass,
            "initial_mass_kg": config.initial_state.m,
            "inertia_kg_m2": config.vehicle.nominal_inertia,
            "max_thrust_n": config.vehicle.max_thrust,
            "min_thrust_n": config.vehicle.min_thrust,
            "gimbal_limit_deg": math.degrees(config.vehicle.actuator_limits.max_gimbal_angle_rad),
            "gimbal_rate_limit_deg_s": math.degrees(config.vehicle.actuator_limits.gimbal_rate_limit_rad_s),
            "rcs_torque_limit_n_m": config.vehicle.actuator_limits.max_rcs_torque,
            "mass_flow_enabled": config.vehicle.enable_mass_depletion,
            "variable_inertia_enabled": config.vehicle.enable_variable_inertia,
            "drag_enabled": config.vehicle.enable_drag,
            "wind_enabled": config.vehicle.enable_wind,
            "engine_lag_enabled": config.vehicle.enable_engine_lag,
        },
        "initial_state": {
            "x_m": config.initial_state.x,
            "z_m": config.initial_state.z,
            "vx_mps": config.initial_state.vx,
            "vz_mps": config.initial_state.vz,
            "theta_deg": math.degrees(config.initial_state.theta),
            "omega_deg_s": math.degrees(config.initial_state.omega),
        },
        "target": {
            "x_m": target.x,
            "z_m": target.z,
            "theta_deg": math.degrees(target.theta),
        },
        "guidance": guidance_dict,
        "controller": {
            "pid": {
                "altitude": {"kp": config.pid.z_velocity.kp, "ki": config.pid.z_velocity.ki, "kd": config.pid.z_velocity.kd},
                "lateral": {"kp": config.pid.x_velocity.kp, "ki": config.pid.x_velocity.ki, "kd": config.pid.x_velocity.kd},
                "attitude": {"kp": config.pid.theta.kp, "ki": config.pid.theta.ki, "kd": config.pid.theta.kd},
            },
            "state_space": {
                "state_vector": list(config.state_space.state_vector) if hasattr(config.state_space, 'state_vector') else ["x", "z", "vx", "vz", "theta", "omega"],
                "input_vector": list(config.state_space.input_vector) if hasattr(config.state_space, 'input_vector') else ["delta_thrust", "pitch_torque"],
                "q_diagonal": list(config.state_space.q_diagonal),
                "r_diagonal": list(config.state_space.r_diagonal),
            },
        },
    }


def config_from_dict(data: dict[str, Any]) -> RuntimeConfig:
    vehicle_data = data.get("vehicle", {})
    initial_data = data.get("initial_state", {})
    simulation_data = data.get("simulation", {})
    controller_mode = data.get("controller_mode", "pid")
    allocator_mode = data.get("allocator_mode", "hybrid")

    dry_mass = float(vehicle_data.get("dry_mass_kg", 1200.0))
    initial_mass = float(vehicle_data.get("initial_mass_kg", max(dry_mass + 250.0, dry_mass)))
    inertia = float(vehicle_data.get("inertia_kg_m2", 920.0))
    max_thrust = float(vehicle_data.get("max_thrust_n", 22000.0))
    min_thrust = float(vehicle_data.get("min_thrust_n", 0.0))
    gimbal_limit_deg = float(vehicle_data.get("gimbal_limit_deg", 10.0))
    gimbal_rate_limit_deg_s = float(vehicle_data.get("gimbal_rate_limit_deg_s", 45.0))
    rcs_limit = float(vehicle_data.get("rcs_torque_limit_n_m", 1500.0))

    vehicle = VehicleParameters(
        dry_mass=dry_mass,
        propellant_mass=max(initial_mass - dry_mass, 0.0),
        dry_inertia=inertia,
        nominal_inertia=inertia,
        max_thrust=max_thrust,
        min_thrust=min_thrust,
        enable_mass_depletion=bool(vehicle_data.get("mass_flow_enabled", True)),
        enable_variable_inertia=bool(vehicle_data.get("variable_inertia_enabled", True)),
        enable_drag=bool(vehicle_data.get("drag_enabled", False)),
        enable_wind=bool(vehicle_data.get("wind_enabled", False)),
        enable_engine_lag=bool(vehicle_data.get("engine_lag_enabled", False)),
        actuator_limits=ActuatorLimits(
            min_throttle=0.0,
            max_throttle=1.0,
            max_gimbal_angle_rad=math.radians(gimbal_limit_deg),
            gimbal_rate_limit_rad_s=math.radians(gimbal_rate_limit_deg_s),
            max_rcs_torque=rcs_limit,
        ),
        touchdown=TouchdownParameters(
            max_vertical_speed=float(simulation_data.get("landing_vz_limit_mps", 2.0)),
            max_horizontal_speed=float(simulation_data.get("landing_vx_limit_mps", 1.0)),
            max_tilt_rad=math.radians(float(simulation_data.get("landing_tilt_limit_deg", 12.0))),
            freeze_on_crash=bool(simulation_data.get("freeze_on_crash", True)),
        ),
    )

    initial_state = LanderState(
        x=float(initial_data.get("x_m", 0.0)),
        z=float(initial_data.get("z_m", 20.0)),
        vx=float(initial_data.get("vx_mps", 0.0)),
        vz=float(initial_data.get("vz_mps", 0.0)),
        theta=math.radians(float(initial_data.get("theta_deg", 0.0))),
        omega=math.radians(float(initial_data.get("omega_deg_s", 0.0))),
        m=initial_mass,
    )

    target = data.get("target", {})
    guidance_data = data.get("guidance", {})
    mission = _mission_from_dict(guidance_data, target)
    pid = _pid_from_dict(data.get("controller", {}).get("pid", {}))
    state_space = _state_space_from_dict(data.get("controller", {}).get("state_space", {}))
    open_loop = OpenLoopSettings(
        throttle=float(data.get("controller", {}).get("open_loop", {}).get("throttle", 0.65)),
        gimbal_deg=float(data.get("controller", {}).get("open_loop", {}).get("gimbal_deg", 0.0)),
        rcs_torque_n_m=float(data.get("controller", {}).get("open_loop", {}).get("rcs_torque_n_m", 0.0)),
    )
    simulation = SimulationSettings(
        dt_s=float(simulation_data.get("dt_s", 0.02)),
        duration_s=float(simulation_data.get("duration_s", 12.0)),
        playback_speed=float(simulation_data.get("playback_speed", 1.0)),
        integrator=str(simulation_data.get("integrator", "rk4")),
    )
    return RuntimeConfig(
        preset_name=str(data.get("preset_name", "Custom")),
        description=str(data.get("description", "Custom configuration")),
        controller_mode=controller_mode,
        allocator_mode=allocator_mode,
        simulation=simulation,
        vehicle=vehicle,
        initial_state=initial_state,
        mission=mission,
        pid=pid,
        state_space=state_space,
        open_loop=open_loop,
    )


def _mission_from_dict(guidance_data: dict[str, Any], target_data: dict[str, Any]) -> MissionProfile:
    mode = guidance_data.get("mode", "hover")
    if mode == "sequence":
        time_cursor = 0.0
        segments: list[GuidanceSegment] = []
        for index, segment in enumerate(guidance_data.get("segments", [])):
            duration = float(segment.get("duration_s", 1.0))
            target = _target_from_dict(segment.get("target", {}), label=segment.get("name", f"segment_{index + 1}"))
            segments.append(GuidanceSegment(start_time=time_cursor, end_time=time_cursor + duration, target=target))
            time_cursor += duration
        if segments:
            return MissionProfile(name="sequence", segments=tuple(segments))
    target = _target_from_dict(target_data, label=str(guidance_data.get("mode", "hover")))
    return MissionProfile(name=str(mode), segments=(GuidanceSegment(0.0, 60.0, target),))


def _target_from_dict(data: dict[str, Any], label: str) -> GuidanceTarget:
    return GuidanceTarget(
        x=float(data.get("x_m", 0.0)),
        z=float(data.get("z_m", 20.0)),
        vx=float(data.get("vx_mps", 0.0)),
        vz=float(data.get("vz_mps", 0.0)),
        theta=math.radians(float(data.get("theta_deg", 0.0))),
        omega=math.radians(float(data.get("omega_deg_s", 0.0))),
        label=label,
    )


def _pid_from_dict(data: dict[str, Any]) -> CascadedPIDConfig:
    altitude = data.get("altitude", {})
    lateral = data.get("lateral", {})
    attitude = data.get("attitude", {})
    return CascadedPIDConfig(
        x_position=PIDAxisGains(0.18, ki=0.0, kd=0.04, output_limit=4.0),
        x_velocity=PIDAxisGains(float(lateral.get("kp", 0.45)), ki=float(lateral.get("ki", 0.0)), kd=float(lateral.get("kd", 0.28)), output_limit=math.radians(15.0)),
        z_position=PIDAxisGains(0.35, ki=0.02, kd=0.08, output_limit=3.0),
        z_velocity=PIDAxisGains(float(altitude.get("kp", 6.0)), ki=float(altitude.get("ki", 1.2)), kd=float(altitude.get("kd", 2.5)), integrator_limit=8.0, output_limit=10.0),
        theta=PIDAxisGains(float(attitude.get("kp", 8.0)), ki=float(attitude.get("ki", 0.15)), kd=float(attitude.get("kd", 3.0)), output_limit=4.0),
        omega=PIDAxisGains(900.0, ki=45.0, kd=180.0, integrator_limit=1_000.0, output_limit=6_000.0),
    )


def _state_space_from_dict(data: dict[str, Any]) -> StateSpaceConfig:
    return StateSpaceConfig(
        q_diagonal=tuple(float(v) for v in data.get("q_diagonal", [18.0, 28.0, 10.0, 16.0, 35.0, 12.0])),
        r_diagonal=tuple(float(v) for v in data.get("r_diagonal", [0.18, 0.45])),
    )
