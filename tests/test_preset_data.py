from __future__ import annotations

import json
from pathlib import Path


PRESET_DIR = Path(__file__).resolve().parents[1] / "src" / "lander_sim" / "data" / "presets"
REQUIRED_PRESETS = {
    "stable_hover.json": "pid",
    "poorly_tuned_pid.json": "pid",
    "well_tuned_pid.json": "pid",
    "state_space_hover.json": "state_space",
    "lateral_translation.json": "state_space",
    "landing_mass_depletion.json": "state_space",
    "rcs_pitch_test.json": "state_space",
    "gimbal_pitch_stabilization.json": "pid",
}


def _load_preset(name: str) -> dict:
    return json.loads((PRESET_DIR / name).read_text())


def test_required_presets_exist() -> None:
    assert PRESET_DIR.exists()
    assert {path.name for path in PRESET_DIR.glob("*.json")} >= set(REQUIRED_PRESETS)


def test_preset_schema_contains_core_sections() -> None:
    for file_name, controller_mode in REQUIRED_PRESETS.items():
        preset = _load_preset(file_name)

        assert preset["schema_version"] == 1
        assert preset["preset_name"]
        assert preset["controller_mode"] == controller_mode
        assert preset["simulation"]["dt_s"] > 0.0
        assert preset["simulation"]["duration_s"] > 0.0
        assert preset["vehicle"]["initial_mass_kg"] > preset["vehicle"]["dry_mass_kg"]
        assert "initial_state" in preset
        assert "target" in preset
        assert "controller" in preset


def test_state_space_and_sequence_presets_expose_expected_contracts() -> None:
    hover = _load_preset("state_space_hover.json")
    landing = _load_preset("landing_mass_depletion.json")
    translation = _load_preset("lateral_translation.json")
    rcs = _load_preset("rcs_pitch_test.json")
    gimbal = _load_preset("gimbal_pitch_stabilization.json")

    assert hover["controller"]["state_space"]["state_vector"] == [
        "x",
        "z",
        "vx",
        "vz",
        "theta",
        "omega",
    ]
    assert hover["controller"]["state_space"]["input_vector"] == [
        "delta_thrust",
        "pitch_torque",
    ]
    assert landing["vehicle"]["mass_flow_enabled"] is True
    assert len(landing["guidance"]["segments"]) == 2
    assert len(translation["guidance"]["segments"]) == 3
    assert translation["allocator_mode"] == "hybrid"
    assert rcs["allocator_mode"] == "rcs_only"
    assert gimbal["allocator_mode"] == "gimbal_only"
