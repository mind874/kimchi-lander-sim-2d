# Kimchi Lander Sim 2D

Kimchi Lander Sim 2D is a **desktop-grade engineering simulator** for a planar rocket hop vehicle. It is built to compare **open-loop**, **cascaded PID**, and **state-space / LQR-style full-state feedback** controllers on the same nonlinear 2D rigid-body model.

This is **not a game**. The goal is an understandable, tunable environment for guidance, control, parameter studies, and visualization.

## Stack

- **Python 3.11+**
- **PySide6** desktop UI
- **pyqtgraph** live plots and overlays
- **NumPy / SciPy** for simulation math, linearization, and LQR design

## Current MVP

The current app includes:

- planar rigid-body dynamics with states `x, z, vx, vz, theta, omega, m`
- fixed-step **RK4** and **Euler** integration
- gravity, thrust-vector transforms, pitch torque, optional mass depletion
- **open-loop**, **PID**, and **state-space** controller modes
- hover / translation / hop-style guidance targets
- editable vehicle, simulation, PID, state-space, and guidance settings
- dark-theme desktop UI with:
  - settings tabs
  - 2D scene renderer
  - live playback controls
  - synchronized plots
  - analytics summary
- built-in presets for hover, poor/well tuned PID, state-space hover, translation, landing with depletion, RCS-only pitch test, and gimbaled-engine pitch stabilization
- save/load JSON configurations
- retained-run comparison overlays

## Project layout

```text
src/lander_sim/
├── dynamics/      # plant, integrators, linearization, state/parameter models
├── control/       # PID, state-space, guidance, actuator allocation
├── simulation/    # runner, history, analytics, presets/config parsing
├── ui/            # main window, scene renderer, panels, plotting, playback
├── data/presets/  # shipped JSON presets
└── utils/         # config IO and math/unit helpers
```

## Model assumptions and simplifications

The simulator is intentionally explicit and readable, but still simplified:

- **2D planar only** — no roll, yaw, or 3D coupling
- **Rigid body** — no structural flexibility or slosh model
- **Flat ground plane** — touchdown classification rather than a full contact solver
- **State-space controller is local to hover trim** — it uses a hover linearization and mass-aware thrust feedforward, but it is still a linear controller around a nominal operating condition
- **Actuator allocation is explicit** — the controller requests abstract thrust / pitch torque, and the allocator maps that into gimbal-only, RCS-only, or hybrid actuation
- **Optional fidelity hooks** — drag, wind, engine lag, CG/inertia variation, observers, Monte Carlo, and 3D expansion are intentionally left as future seams

## Engineering note

The nonlinear plant and the linearized hover model are intentionally separated:

- `dynamics/vehicle_model.py` contains the nonlinear planar equations used for simulation
- `dynamics/linearization.py` contains the hover-trim linear model used by the state-space controller
- `control/state_space_controller.py` exposes the controller matrices and closed-loop poles used in the UI

That separation is deliberate so future work can add higher-fidelity plant effects without hiding what the linear controller is actually designed against.

## Running locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e . pytest
python -m lander_sim
```

## Verification

```bash
source .venv/bin/activate
python -m compileall src tests
pytest -q
QT_QPA_PLATFORM=offscreen python - <<'PY'
from PySide6.QtWidgets import QApplication
from lander_sim.ui.main_window import MainWindow
app = QApplication.instance() or QApplication([])
window = MainWindow()
window.run_simulation()
print(window.current_result.run_name, len(window.current_result.samples))
window.close()
PY
```

## Presets

Built-in presets live in `src/lander_sim/data/presets/`:

- `stable_hover.json`
- `poorly_tuned_pid.json`
- `well_tuned_pid.json`
- `state_space_hover.json`
- `lateral_translation.json`
- `landing_mass_depletion.json`
- `rcs_pitch_test.json`
- `gimbal_pitch_stabilization.json`

## Future extensions

Planned extension seams already exist for:

- gain scheduling improvements
- estimator / Kalman filter toggles
- Monte Carlo batches
- richer actuator / engine dynamics
- CSV / plot export polish
- higher-fidelity contact and eventually 3D dynamics
