from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from lander_sim.control.state_space_controller import StateSpaceController
from lander_sim.simulation.runner import SimulationRunner
from lander_sim.simulation.scenarios import (
    RuntimeConfig,
    config_from_dict,
    config_to_dict,
    find_preset_path,
    list_preset_summaries,
    load_config,
)


def serialize_runtime_config(config: RuntimeConfig) -> dict[str, Any]:
    return config_to_dict(config)


def controller_details(config: RuntimeConfig) -> dict[str, Any]:
    if config.controller_mode == "state_space":
        controller = StateSpaceController(config.vehicle, config.simulation.dt_s, config.state_space)
        return {
            "kind": "state_space",
            "state_labels": list(controller.state_labels),
            "input_labels": list(controller.input_labels),
            "A": controller.A.tolist(),
            "B": controller.B.tolist(),
            "Ad": controller.Ad.tolist(),
            "Bd": controller.Bd.tolist(),
            "K": controller.K.tolist(),
            "closed_loop_poles": [
                {"real": float(value.real), "imag": float(value.imag)} for value in controller.closed_loop_poles
            ],
        }
    return {
        "kind": "pid" if config.controller_mode == "pid" else "open_loop",
        "loops": {
            "horizontal_position_to_velocity": "x position -> x velocity target",
            "horizontal_velocity_to_attitude": "x velocity -> theta target",
            "attitude_to_torque": "theta/omega -> pitch torque",
            "vertical_position_to_velocity": "z position -> z velocity target",
            "vertical_velocity_to_thrust": "z velocity -> thrust",
        },
        "gains": {
            "lateral": {
                "kp": config.pid.x_velocity.kp,
                "ki": config.pid.x_velocity.ki,
                "kd": config.pid.x_velocity.kd,
            },
            "altitude": {
                "kp": config.pid.z_velocity.kp,
                "ki": config.pid.z_velocity.ki,
                "kd": config.pid.z_velocity.kd,
            },
            "attitude": {
                "kp": config.pid.theta.kp,
                "ki": config.pid.theta.ki,
                "kd": config.pid.theta.kd,
            },
        },
    }


def run_simulation(config_payload: dict[str, Any]) -> dict[str, Any]:
    config = config_from_dict(config_payload)
    result = SimulationRunner(config).run()
    result.metadata.setdefault("vehicle_length_m", config.vehicle.vehicle_length_m)
    result.metadata.setdefault("allocator_mode", config.allocator_mode)
    result.metadata.setdefault("preset_description", config.description)
    return {
        "config": serialize_runtime_config(config),
        "controller_details": controller_details(config),
        "run": result.to_dict(),
    }


def parse_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.config_json:
        return json.loads(args.config_json)
    if args.config_file:
        return json.loads(Path(args.config_file).read_text())
    data = sys.stdin.read().strip()
    if not data:
        raise ValueError("Expected config payload via --config-json, --config-file, or stdin")
    return json.loads(data)


def command_list_presets(_args: argparse.Namespace) -> None:
    print(json.dumps({"presets": list_preset_summaries()}))


def command_get_preset(args: argparse.Namespace) -> None:
    path = find_preset_path(args.identifier)
    config = load_config(path)
    print(json.dumps({"preset": serialize_runtime_config(config), "file_name": path.name}))


def command_run(args: argparse.Namespace) -> None:
    payload = parse_payload(args)
    print(json.dumps(run_simulation(payload)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bridge the Python simulation core to Electron/React frontends")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-presets", help="List built-in presets")
    list_parser.set_defaults(func=command_list_presets)

    get_parser = subparsers.add_parser("get-preset", help="Load a built-in preset by file name or preset name")
    get_parser.add_argument("identifier")
    get_parser.set_defaults(func=command_get_preset)

    run_parser = subparsers.add_parser("run", help="Run a simulation from a JSON config payload")
    run_parser.add_argument("--config-json")
    run_parser.add_argument("--config-file")
    run_parser.set_defaults(func=command_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except Exception as exc:  # pragma: no cover - CLI error path
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
