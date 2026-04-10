from __future__ import annotations

from math import isclose, sqrt

from lander_sim.simulation.analytics import build_comparison_entries, compute_run_analytics


def _nominal_run() -> dict:
    return {
        "metadata": {
            "run_name": "pid-hover-a",
            "preset_name": "Stable Hover",
            "controller_mode": "pid",
            "target": {"x_m": 0.0, "z_m": 20.0},
            "actuator_limits": {
                "throttle_max": 1.0,
                "gimbal_limit_rad": 0.1,
                "rcs_torque_limit_nm": 1.0,
            },
        },
        "state_history": {
            "x": [0.6, 0.2, 0.05, 0.0],
            "z": [20.6, 20.2, 20.05, 20.0],
            "vx": [-0.5, -0.2, -0.05, 0.0],
            "vz": [-0.8, -0.35, -0.15, 0.0],
            "theta": [0.08, 0.05, 0.02, 0.0],
            "mass": [1450.0, 1445.0, 1440.0, 1435.0],
        },
        "command_history": {
            "throttle": [0.8, 1.0, 0.95, 0.72],
            "gimbal": [0.0, 0.05, 0.1, 0.02],
            "rcs_left": [0.0, 1.0, 0.0, 1.0],
            "rcs_right": [0.0, 0.0, 1.0, 0.0],
        },
        "events": [{"name": "touchdown", "index": 2}],
    }


def test_compute_run_analytics_reports_touchdown_metrics() -> None:
    analytics = compute_run_analytics(_nominal_run())

    assert analytics.run_name == "pid-hover-a"
    assert analytics.preset_name == "Stable Hover"
    assert analytics.controller_mode == "pid"
    assert isclose(analytics.final_position_error_m, 0.0)
    assert analytics.touchdown_velocity_mps is not None
    assert isclose(
        analytics.touchdown_velocity_mps,
        sqrt(0.05**2 + 0.15**2),
        rel_tol=1e-9,
    )
    assert isclose(analytics.peak_angle_deg, 0.08 * 180.0 / 3.141592653589793, rel_tol=1e-9)
    assert isclose(analytics.fuel_consumed_kg, 15.0)
    assert analytics.rcs_pulse_count == 3
    assert isclose(analytics.saturation_fraction, 0.5)
    assert analytics.landing_pass is True
    assert analytics.event_flags == ("touchdown",)
    assert analytics.target_position_m == (0.0, 20.0)


def test_compute_run_analytics_detects_failed_landing() -> None:
    failing_run = _nominal_run()
    failing_run["metadata"] = {
        **failing_run["metadata"],
        "run_name": "bad-landing",
        "target": {"x_m": 0.0, "z_m": 0.0},
    }
    failing_run["state_history"] = {
        **failing_run["state_history"],
        "x": [2.0, 1.4, 1.0, 0.8],
        "z": [5.0, 1.0, 0.2, 0.0],
        "vx": [-2.0, -1.5, -1.2, -1.0],
        "vz": [-3.5, -3.2, -2.6, -2.0],
        "theta": [0.25, 0.2, 0.12, 0.1],
    }
    failing_run["events"] = [
        {"name": "touchdown", "index": 2},
        {"name": "crash"},
    ]

    analytics = compute_run_analytics(failing_run)

    assert analytics.touchdown_velocity_mps is not None
    assert analytics.touchdown_velocity_mps > 2.0
    assert analytics.final_position_error_m > 0.5
    assert analytics.peak_angle_deg > 10.0
    assert analytics.landing_pass is False
    assert analytics.event_flags == ("touchdown", "crash")


def test_build_comparison_entries_preserves_run_metadata() -> None:
    run_a = _nominal_run()
    run_b = _nominal_run()
    run_b["metadata"] = {
        **run_b["metadata"],
        "run_name": "lqr-hover-b",
        "preset_name": "State-Space Hover",
        "controller_mode": "state_space",
    }

    entries = build_comparison_entries([run_a, run_b])

    assert entries[0].label == "pid-hover-a [pid]"
    assert entries[0].preset_name == "Stable Hover"
    assert entries[1].label == "lqr-hover-b [state_space]"
    assert entries[1].preset_name == "State-Space Hover"
