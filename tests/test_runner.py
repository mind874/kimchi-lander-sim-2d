from __future__ import annotations

from lander_sim.simulation.runner import SimulationRunner
from lander_sim.simulation.scenarios import default_runtime_config



def test_runner_produces_samples_and_analytics() -> None:
    config = default_runtime_config()
    result = SimulationRunner(config).run()
    assert result.samples
    assert result.analytics is not None
    assert result.state_history['time'][0] == 0.0
