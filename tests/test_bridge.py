from __future__ import annotations

from lander_sim.bridge import controller_details, run_simulation, serialize_runtime_config
from lander_sim.simulation.scenarios import default_runtime_config



def test_bridge_serializes_default_runtime_config() -> None:
    config = default_runtime_config()
    payload = serialize_runtime_config(config)
    assert payload['preset_name'] == 'Stable Hover'
    assert payload['simulation']['dt_s'] > 0.0



def test_bridge_returns_state_space_details_for_state_space_runs() -> None:
    config = serialize_runtime_config(default_runtime_config())
    config['controller_mode'] = 'state_space'
    result = run_simulation(config)
    assert result['controller_details']['kind'] == 'state_space'
    assert len(result['controller_details']['A']) == 6
    assert len(result['run']['samples']) > 0



def test_bridge_returns_pid_loop_metadata_for_pid_runs() -> None:
    config = serialize_runtime_config(default_runtime_config())
    result = run_simulation(config)
    assert result['controller_details']['kind'] == 'pid'
    assert 'horizontal_position_to_velocity' in result['controller_details']['loops']
