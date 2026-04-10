from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from lander_sim.control.guidance import GuidanceTarget
from lander_sim.dynamics.state import AbstractControlCommand, ActuatorCommand, LanderState, PlantForces


@dataclass(slots=True, frozen=True)
class SimulationSample:
    time_s: float
    state: LanderState
    target: GuidanceTarget
    abstract_command: AbstractControlCommand
    actuator_command: ActuatorCommand
    forces: PlantForces
    saturated: bool = False
    events: tuple[dict[str, Any], ...] = ()


@dataclass(slots=True)
class RunResult:
    run_name: str
    preset_name: str
    controller_mode: str
    allocator_mode: str
    samples: list[SimulationSample] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    analytics: Any | None = None

    def append(self, sample: SimulationSample) -> None:
        self.samples.append(sample)
        self.events.extend(sample.events)

    @property
    def state_history(self) -> dict[str, list[float]]:
        return {
            "x": [sample.state.x for sample in self.samples],
            "z": [sample.state.z for sample in self.samples],
            "vx": [sample.state.vx for sample in self.samples],
            "vz": [sample.state.vz for sample in self.samples],
            "theta": [sample.state.theta for sample in self.samples],
            "omega": [sample.state.omega for sample in self.samples],
            "mass": [sample.state.m for sample in self.samples],
            "time": [sample.time_s for sample in self.samples],
        }

    @property
    def command_history(self) -> dict[str, list[float]]:
        return {
            "throttle": [sample.actuator_command.metadata.get("throttle", 0.0) for sample in self.samples],
            "gimbal": [sample.actuator_command.gimbal_angle for sample in self.samples],
            "rcs_pitch": [sample.actuator_command.rcs_torque for sample in self.samples],
            "saturated": [1.0 if sample.saturated else 0.0 for sample in self.samples],
            "thrust": [sample.actuator_command.thrust for sample in self.samples],
            "delta_thrust": [sample.abstract_command.debug.get("delta_thrust", 0.0) for sample in self.samples],
        }

    @property
    def target_history(self) -> dict[str, list[float]]:
        return {
            "x": [sample.target.x for sample in self.samples],
            "z": [sample.target.z for sample in self.samples],
            "vx": [sample.target.vx for sample in self.samples],
            "vz": [sample.target.vz for sample in self.samples],
            "theta": [sample.target.theta for sample in self.samples],
        }

    def to_analytics_input(self) -> dict[str, Any]:
        metadata = {
            **self.metadata,
            "run_name": self.run_name,
            "preset_name": self.preset_name,
            "controller_mode": self.controller_mode,
        }
        return {
            "metadata": metadata,
            "state_history": self.state_history,
            "command_history": self.command_history,
            "events": self.events,
        }
