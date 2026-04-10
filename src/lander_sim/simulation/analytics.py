"""Post-run analytics helpers for the 2D lander simulator.

The functions in this module are intentionally UI-agnostic and accept either
dictionary-backed run results or attribute-based objects. This keeps the
simulation lane free to use dataclasses, namedtuples, or richer domain objects
while still allowing analytics, tests, and documentation to share one contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class LandingThresholds:
    """Pass/fail thresholds for a nominal landing result."""

    max_position_error_m: float = 1.0
    max_touchdown_speed_mps: float = 2.0
    max_peak_angle_deg: float = 10.0


@dataclass(frozen=True)
class RunAnalytics:
    """Computed metrics for a completed simulation run."""

    run_name: str
    preset_name: str
    controller_mode: str
    final_position_error_m: float
    touchdown_velocity_mps: float | None
    peak_angle_deg: float
    fuel_consumed_kg: float
    rcs_pulse_count: int
    saturation_fraction: float
    landing_pass: bool
    event_flags: tuple[str, ...]
    target_position_m: tuple[float, float]


@dataclass(frozen=True)
class ComparisonEntry:
    """Minimal metadata needed to label and compare retained runs."""

    run_name: str
    preset_name: str
    controller_mode: str
    label: str


def compute_run_analytics(
    run_result: Any,
    thresholds: LandingThresholds | None = None,
) -> RunAnalytics:
    """Compute task-scoped analytics for a completed run result."""

    thresholds = thresholds or LandingThresholds()
    metadata = _as_mapping(_get_value(run_result, "metadata", default={}))
    state_history = _get_value(run_result, "state_history", "states", default={})
    command_history = _get_value(run_result, "command_history", "commands", default={})
    events = list(_iter_events(_get_value(run_result, "events", default=[])))

    x = _series(state_history, "x", "x_m")
    z = _series(state_history, "z", "z_m")
    vx = _series(state_history, "vx", "vx_mps")
    vz = _series(state_history, "vz", "vz_mps")
    theta = _series(state_history, "theta", "theta_rad")
    mass = _series(state_history, "mass", "mass_kg", "m")

    target = _target_position(metadata)
    final_x = x[-1] if x else target[0]
    final_z = z[-1] if z else target[1]
    final_position_error_m = sqrt((final_x - target[0]) ** 2 + (final_z - target[1]) ** 2)

    touchdown_velocity_mps = _touchdown_velocity(events, vx, vz)
    peak_angle_deg = max((abs(value) * 180.0 / pi for value in theta), default=0.0)
    fuel_consumed_kg = max((mass[0] - mass[-1]) if len(mass) >= 2 else 0.0, 0.0)
    rcs_pulse_count = _rcs_pulse_count(command_history)
    saturation_fraction = _saturation_fraction(command_history, metadata)
    event_flags = tuple(_event_name(event) for event in events if _event_name(event))

    crash_detected = any(name in {"crash", "hard_landing"} for name in event_flags)
    touchdown_detected = any(name in {"touchdown", "landing"} for name in event_flags)
    landing_pass = bool(
        touchdown_detected
        and not crash_detected
        and touchdown_velocity_mps is not None
        and touchdown_velocity_mps <= thresholds.max_touchdown_speed_mps
        and final_position_error_m <= thresholds.max_position_error_m
        and peak_angle_deg <= thresholds.max_peak_angle_deg
    )

    return RunAnalytics(
        run_name=str(
            metadata.get("run_name")
            or metadata.get("name")
            or metadata.get("preset_name")
            or "run"
        ),
        preset_name=str(metadata.get("preset_name") or metadata.get("preset") or "custom"),
        controller_mode=str(
            metadata.get("controller_mode")
            or metadata.get("controller")
            or "unknown"
        ),
        final_position_error_m=final_position_error_m,
        touchdown_velocity_mps=touchdown_velocity_mps,
        peak_angle_deg=peak_angle_deg,
        fuel_consumed_kg=fuel_consumed_kg,
        rcs_pulse_count=rcs_pulse_count,
        saturation_fraction=saturation_fraction,
        landing_pass=landing_pass,
        event_flags=event_flags,
        target_position_m=target,
    )


def build_comparison_entries(run_results: Iterable[Any]) -> tuple[ComparisonEntry, ...]:
    """Build stable comparison labels while preserving run metadata."""

    entries: list[ComparisonEntry] = []
    for run_result in run_results:
        metadata = _as_mapping(_get_value(run_result, "metadata", default={}))
        run_name = str(
            metadata.get("run_name")
            or metadata.get("name")
            or metadata.get("preset_name")
            or "run"
        )
        preset_name = str(metadata.get("preset_name") or metadata.get("preset") or "custom")
        controller_mode = str(
            metadata.get("controller_mode")
            or metadata.get("controller")
            or "unknown"
        )
        label = f"{run_name} [{controller_mode}]"
        entries.append(
            ComparisonEntry(
                run_name=run_name,
                preset_name=preset_name,
                controller_mode=controller_mode,
                label=label,
            )
        )
    return tuple(entries)


def _get_value(container: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if isinstance(container, Mapping) and name in container:
            return container[name]
        if hasattr(container, name):
            return getattr(container, name)
    return default


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if value is None:
        return {}
    if hasattr(value, "__dict__"):
        return value.__dict__
    raise TypeError(f"Expected mapping-like metadata, received {type(value)!r}")


def _series(container: Any, *names: str) -> list[float]:
    values = _get_value(container, *names, default=())
    if values is None:
        return []
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes, bytearray)):
        return [float(value) for value in values]
    raise TypeError(f"Expected a numeric series for {names}, received {type(values)!r}")


def _target_position(metadata: Mapping[str, Any]) -> tuple[float, float]:
    direct = _get_value(metadata, "target_position_m")
    if direct is not None:
        x = float(_get_value(direct, "x", "x_m", default=0.0))
        z = float(_get_value(direct, "z", "z_m", default=0.0))
        return (x, z)

    target = _get_value(metadata, "target")
    if target is not None:
        x = float(_get_value(target, "x", "x_m", default=0.0))
        z = float(_get_value(target, "z", "z_m", default=0.0))
        return (x, z)

    return (
        float(metadata.get("target_x_m", 0.0)),
        float(metadata.get("target_z_m", 0.0)),
    )


def _iter_events(raw_events: Any) -> Iterable[Any]:
    if raw_events is None:
        return ()
    if isinstance(raw_events, Sequence) and not isinstance(raw_events, (str, bytes, bytearray)):
        return raw_events
    return (raw_events,)


def _event_name(event: Any) -> str:
    if isinstance(event, str):
        return event
    name = _get_value(event, "name", "event", "type", default="")
    return str(name)


def _touchdown_velocity(events: Sequence[Any], vx: Sequence[float], vz: Sequence[float]) -> float | None:
    for event in events:
        name = _event_name(event)
        if name not in {"touchdown", "landing"}:
            continue
        explicit_speed = _get_value(event, "touchdown_velocity_mps", "speed_mps", default=None)
        if explicit_speed is not None:
            return float(explicit_speed)

        index = _get_value(event, "index", "sample_index", default=None)
        if index is None:
            break
        touchdown_index = max(0, min(int(index), min(len(vx), len(vz)) - 1))
        if touchdown_index >= 0 and vx and vz:
            return sqrt(vx[touchdown_index] ** 2 + vz[touchdown_index] ** 2)
    return None


def _count_rising_edges(series: Sequence[float], threshold: float = 0.5) -> int:
    active = False
    count = 0
    for value in series:
        now_active = abs(value) > threshold
        if now_active and not active:
            count += 1
        active = now_active
    return count


def _rcs_pulse_count(command_history: Any) -> int:
    left = _series(command_history, "rcs_left", "rcs_left_cmd")
    right = _series(command_history, "rcs_right", "rcs_right_cmd")
    if left or right:
        return _count_rising_edges(left) + _count_rising_edges(right)

    pitch = _series(command_history, "rcs_pitch", "rcs_torque_cmd", "rcs_cmd")
    if pitch:
        return _count_rising_edges(pitch, threshold=1e-6)
    return 0


def _saturation_fraction(command_history: Any, metadata: Mapping[str, Any]) -> float:
    explicit = _series(command_history, "saturated", "saturation_flags")
    if explicit:
        return sum(1.0 for value in explicit if value > 0.5) / len(explicit)

    limits = _as_mapping(metadata.get("actuator_limits", {}))
    channels = [
        _normalized_channel(
            _series(command_history, "throttle", "throttle_cmd"),
            limit=float(limits.get("throttle_max", 1.0)) or 1.0,
            symmetric=False,
        ),
        _normalized_channel(
            _series(command_history, "gimbal", "gimbal_cmd", "gimbal_rad"),
            limit=float(limits.get("gimbal_max", limits.get("gimbal_limit_rad", 1.0))) or 1.0,
        ),
        _normalized_channel(
            _series(command_history, "rcs_pitch", "rcs_torque_cmd", "rcs_cmd"),
            limit=float(limits.get("rcs_max", limits.get("rcs_torque_limit_nm", 1.0))) or 1.0,
        ),
    ]
    sample_count = max((len(channel) for channel in channels), default=0)
    if sample_count == 0:
        return 0.0

    saturated_samples = 0
    for index in range(sample_count):
        if any(_is_sample_saturated(channel, index) for channel in channels if channel):
            saturated_samples += 1
    return saturated_samples / sample_count


def _normalized_channel(
    values: Sequence[float],
    *,
    limit: float,
    symmetric: bool = True,
) -> list[float]:
    if not values:
        return []
    scale = abs(limit) if abs(limit) > 1e-9 else 1.0
    if symmetric:
        return [abs(value) / scale for value in values]
    return [value / scale for value in values]


def _is_sample_saturated(channel: Sequence[float], index: int) -> bool:
    if index >= len(channel):
        return False
    value = channel[index]
    return value >= 0.999
