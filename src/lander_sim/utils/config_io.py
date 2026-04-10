from __future__ import annotations

from pathlib import Path

from lander_sim.simulation.scenarios import RuntimeConfig, load_config, save_config


def load_runtime_config(path: str | Path) -> RuntimeConfig:
    return load_config(Path(path))


def save_runtime_config(config: RuntimeConfig, path: str | Path) -> None:
    save_config(config, Path(path))
