# Kimchi Lander Sim 2D

Kimchi Lander Sim 2D is a **desktop-grade engineering simulator** for a planar rocket hop vehicle. It compares **open-loop**, **cascaded PID**, and **state-space / LQR-style full-state feedback** controllers on the same nonlinear 2D rigid-body model.

This is **not a game**. The primary user experience is now the **Electron + React cockpit**. The Python package remains the simulation/control authority and exposes the bridge used by the frontend.

## Primary frontend: Electron + React

Fastest setup and launch:

```bash
npm start
```

That now uses the safer built-Electron path by default.

Equivalent direct script:

```bash
./scripts/start-app.sh
```

Setup only (without launching):

```bash
npm run setup
```

Development mode with the Vite dev server:

```bash
npm run dev
```

Low-level Electron commands:

```bash
npm run electron:build
npm run electron:start
npm run electron:dev
```

## Python role in the product

Python remains the source of truth for:

- nonlinear planar dynamics
- hover linearization
- PID / state-space controller implementation
- preset loading and config serialization
- simulation execution and analytics

The Python entrypoint no longer launches a separate PySide GUI. Instead:

```bash
python -m lander_sim
```

prints launch guidance, and:

```bash
python -m lander_sim bridge list-presets
python -m lander_sim bridge get-preset stable_hover.json
python -m lander_sim bridge run --config-file path/to/config.json
```

accesses the bridge CLI directly.

## Stack

- **Python 3.11+**
- **Electron** desktop shell
- **React + Vite** renderer
- **NumPy / SciPy** for simulation math, linearization, and LQR design

## Current MVP

The current app includes:

- planar rigid-body dynamics with states `x, z, vx, vz, theta, omega, m`
- fixed-step **RK4** and **Euler** integration
- gravity, thrust-vector transforms, pitch torque, optional mass depletion
- **open-loop**, **PID**, and **state-space** controller modes
- hover / translation / hop-style guidance targets
- editable vehicle, simulation, PID, state-space, and guidance settings
- Electron/React engineering cockpit with:
  - preset/config dock
  - mission/config editor
  - control-law editor
  - world view and playback scrubber
  - retained-run comparison bank
  - controller inspector
  - synchronized plots and analytics
- built-in presets for hover, poor/well tuned PID, state-space hover, translation, landing with depletion, RCS-only pitch test, and gimbaled-engine pitch stabilization
- save/load JSON configurations
- retained-run comparison overlays

## Project layout

```text
src/lander_sim/
├── dynamics/      # plant, integrators, linearization, state/parameter models
├── control/       # PID, state-space, guidance, actuator allocation
├── simulation/    # runner, history, analytics, presets/config parsing
├── data/presets/  # shipped JSON presets
├── bridge.py      # Python bridge used by the Electron frontend
└── utils/         # config IO and math/unit helpers

electron-app/
├── electron/      # main/preload shell
├── src/app/       # app shell + state hooks
├── src/features/  # feature-sliced renderer modules
├── src/shared/    # bridge adapters and helpers
└── src/components/# shared visualization components
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
- `control/state_space_controller.py` exposes the controller matrices and closed-loop poles used by the frontend inspector
- `bridge.py` is the only supported interface from the JS frontend into Python runtime behavior

This keeps the React/Electron shell thin and avoids forking simulator logic into JavaScript.

## Verification

```bash
npm run python:test
npm run bridge:list-presets
npm run electron:build
```

Direct bridge verification example:

```bash
source .venv/bin/activate
python -m lander_sim bridge list-presets
python -m lander_sim bridge get-preset stable_hover.json
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
- packaged Electron distribution with bundled Python runtime
