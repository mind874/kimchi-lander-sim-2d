# PRD — Desktop-Grade 2D Rocket Lander Engineering Simulator

**Status:** Consensus plan, approved for execution handoff  
**Date:** 2026-04-10  
**Context snapshot:** `.omx/context/desktop-grade-2d-rocket-lander-sim-20260410T063446Z.md`

## 1) Requirements Summary

Build a polished local desktop engineering tool for a planar rocket lander / hop vehicle. The tool is explicitly **not a game**. It must support:

- planar rigid-body simulation with clear SI-unit math
- open-loop, PID, and genuine state-space/full-state feedback control
- real-time and post-run visualization
- live tuning of vehicle, scenario, and controller parameters
- save/load presets and compare multiple runs on the same plant
- a code structure that can extend toward higher-fidelity and eventually 3D dynamics

The repository is currently greenfield except for `.omx/` runtime metadata.

## 2) RALPLAN-DR Summary

### Principles
1. **Explicit math over hidden behavior** — state definitions, forces, moments, linearization, and controller equations must be inspectable in code and surfaced in the UI where relevant.
2. **Deterministic simulation first** — fixed-step integration, reproducible presets, and immutable run histories are mandatory for controller comparison.
3. **Desktop-native responsiveness** — choose the stack that minimizes latency and synchronization overhead for live tuning, plotting, and playback.
4. **Extensible boundaries** — keep plant, controllers, analytics, and UI adapters separate so future estimators, Monte Carlo, and higher-fidelity physics do not require a rewrite.
5. **MVP before extras** — deliver a credible engineering sandbox before advanced features like observers, sweeps, or export automation.

### Decision Drivers
1. High-quality real-time plotting and responsive desktop interaction
2. Numerical clarity and low-maintenance architecture
3. Honest PID-vs-state-space comparison on the same vehicle model

### Viable Options

#### Option A — Pure Python desktop app: PySide6 + pyqtgraph + NumPy/SciPy
**Pros**
- Single-language stack for simulation, controls, and UI integration
- Strong real-time plotting and mature desktop layout primitives
- No Electron/Python IPC boundary
- Lowest complexity path to an MVP with polished local UX

**Cons**
- Requires deliberate Qt theming and custom scene rendering to look premium
- Less direct path to future browser deployment

#### Option B — Electron frontend + Python simulation service
**Pros**
- Flexible web-style presentation layer
- Easier future path if a browser-deliverable UI becomes the priority

**Cons**
- Cross-process synchronization and packaging complexity
- Higher latency and more duplicated state management for live runs
- Larger implementation surface before the first usable MVP

### Recommendation
Choose **Option A**. Use a **pure Python desktop stack**:

- **PySide6** for the application shell and panels
- **pyqtgraph** for live plots and comparison overlays
- **NumPy/SciPy** for simulation math, linearization, discretization, and LQR/state feedback

Option B remains a viable future migration path, but it is weaker for the requested first delivery because it adds architectural complexity without improving the core engineering workflow.

## 3) Architecture Summary

### Stack Decision
- **Language:** Python 3.11+
- **UI:** PySide6
- **Plotting:** pyqtgraph
- **Numerics:** NumPy + SciPy
- **Serialization:** stdlib JSON + typed dataclasses
- **Testing:** pytest + offscreen Qt smoke launch

### Architectural Shape
- `dynamics/`: explicit plant equations, integrators, linearization, disturbances
- `control/`: PID, state-space, guidance, actuator allocation
- `simulation/`: run loop, history buffers, analytics, scenarios
- `ui/`: Qt shell, scene renderer, settings panels, plots, status bar
- `data/presets/`: scenario/controller presets
- `utils/`: config IO, unit helpers, shared math

### Execution / Thread Model
- The simulation core runs in a dedicated Qt worker (`QThread`) or worker object with signal-based updates.
- The UI never mutates simulation state directly; it submits a config snapshot and receives emitted history samples / run completion results.
- Every run produces an immutable `RunResult` with:
  - sampled state history
  - sampled command history
  - event flags (touchdown, crash, saturation)
  - metadata (preset name, controller mode, dt, nominal mass, allocator mode)

### Plant and Control Boundaries
- Nonlinear plant state: `[x, z, vx, vz, theta, omega, m]`
- Optional extended properties live in parameter/config objects, not the core minimal state:
  - `cg_offset`
  - variable `Iyy`
  - wind
  - engine lag
- State-space controller uses a hover-trim linear model with visible:
  - continuous-time `A`, `B`
  - sampled `Ad`, `Bd` at the control timestep
  - user-editable `Q`, `R` or direct `K`
  - computed closed-loop poles/eigenvalues
- The state-space control law outputs **abstract** commands `[ΔT, τ_pitch]`.
- `control/actuator_allocator.py` maps `[ΔT, τ_pitch]` into:
  - gimbal-only
  - RCS-only
  - hybrid

This preserves a genuine state-space controller while keeping actuator comparisons honest and explicit.

## 4) ADR

### Decision
Build the MVP as a **pure Python desktop application** with a **modular simulation core** and **Qt-based UI**.

### Drivers
- Lowest-latency path to real-time simulation + plotting
- Fewer moving parts for a greenfield engineering application
- Easier to keep plant/controller code and UI code decoupled but synchronous enough for live tuning

### Alternatives considered
- Electron + Python backend
- A more minimal Python plotting stack (e.g. matplotlib-heavy UI)

### Why chosen
- Electron adds IPC, packaging, and state-sync complexity early.
- Matplotlib-centered desktop UX is weaker for continuous live updates and interactive engineering tuning.
- PySide6 + pyqtgraph fits the requirement for a polished, responsive, maintainable local engineering tool.

### Consequences
- The app stays desktop-native for MVP instead of browser-native.
- Scene rendering and theming quality must be handled intentionally in the UI layer.
- The simulation core must remain headless and serializable to preserve a future migration path.

### Follow-ups
- Leave clear seams for future observer/Kalman, Monte Carlo, and 3D model packages.
- Keep `RunResult` and controller config schemas stable so future alternate frontends can consume them.

## 5) Proposed File Tree

```text
kimchi-lander-sim-2d/
├── README.md
├── pyproject.toml
├── src/
│   └── lander_sim/
│       ├── __init__.py
│       ├── __main__.py
│       ├── app.py
│       ├── dynamics/
│       │   ├── __init__.py
│       │   ├── state.py
│       │   ├── parameters.py
│       │   ├── vehicle_model.py
│       │   ├── integrators.py
│       │   ├── linearization.py
│       │   └── disturbances.py
│       ├── control/
│       │   ├── __init__.py
│       │   ├── pid_controller.py
│       │   ├── state_space_controller.py
│       │   ├── guidance.py
│       │   └── actuator_allocator.py
│       ├── simulation/
│       │   ├── __init__.py
│       │   ├── runner.py
│       │   ├── history.py
│       │   ├── analytics.py
│       │   └── scenarios.py
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── main_window.py
│       │   ├── theme.py
│       │   ├── scene_renderer.py
│       │   ├── playback_controller.py
│       │   ├── widgets.py
│       │   ├── panels/
│       │   │   ├── settings_panel.py
│       │   │   ├── vehicle_panel.py
│       │   │   ├── sim_panel.py
│       │   │   ├── pid_panel.py
│       │   │   ├── state_space_panel.py
│       │   │   ├── guidance_panel.py
│       │   │   ├── presets_panel.py
│       │   │   └── analytics_panel.py
│       │   └── plotting/
│       │       ├── plot_manager.py
│       │       └── comparison_plot_widget.py
│       ├── data/
│       │   └── presets/
│       │       ├── stable_hover.json
│       │       ├── poorly_tuned_pid.json
│       │       ├── well_tuned_pid.json
│       │       ├── state_space_hover.json
│       │       ├── lateral_translation.json
│       │       ├── landing_mass_depletion.json
│       │       ├── rcs_pitch_test.json
│       │       └── gimbal_pitch_stabilization.json
│       └── utils/
│           ├── __init__.py
│           ├── config_io.py
│           ├── units.py
│           ├── math2d.py
│           └── qt_helpers.py
└── tests/
    ├── test_vehicle_model.py
    ├── test_integrators.py
    ├── test_linearization.py
    ├── test_pid_controller.py
    ├── test_state_space_controller.py
    ├── test_guidance.py
    ├── test_analytics.py
    └── test_smoke_ui.py
```

## 6) Acceptance Criteria

1. **Launch/UI**
   - `python -m lander_sim` opens a dark-theme desktop UI with left settings panels, a center simulation view, and a right/bottom plot + analytics area.
2. **Plant fidelity**
   - The nonlinear model in `src/lander_sim/dynamics/vehicle_model.py` simulates `x, z, vx, vz, theta, omega, m` with gravity and thrust-body/world transforms.
   - Optional drag, mass depletion, variable inertia, wind, and engine lag are toggled through config without changing plant code paths elsewhere.
3. **Controller modes**
   - Users can switch between open-loop, PID, and state-space modes from the UI.
   - The PID implementation explicitly exposes the loop structure and anti-windup controls.
   - The state-space implementation explicitly exposes state vector, input vector, `A/B`, `Q/R` or `K`, and closed-loop poles.
4. **Visualization**
   - The scene view shows body, thrust vector, gimbal indication, RCS indication, target marker, ground line, and trajectory trail.
   - Plots update during runs for position, velocity, attitude, angular rate, mass, and command channels.
5. **Tuning / presets**
   - Vehicle, simulation, guidance, PID, and state-space parameters are editable live and can be saved/loaded as JSON configs.
   - At least these presets are shipped: stable hover, poorly tuned PID, well tuned PID, state-space hover, lateral translation, landing with mass depletion.
6. **Comparison**
   - Users can retain at least two named runs and overlay their histories in the comparison plot view.
7. **Analytics**
   - Post-run analytics compute final position error, touchdown velocity, peak angle, fuel consumed, RCS pulse count, saturation fraction, and landing pass/fail.
8. **Numerical hygiene**
   - Negative mass, actuator limit violations, and ground penetration are clamped/handled explicitly with logged events.
9. **Verification**
   - Automated tests cover plant math, integrators, PID behavior, linearization/state-space behavior, analytics metrics, and a UI smoke launch.

## 7) Implementation Steps

### Phase 1 — Bootstrap and shared config
**Files**
- `pyproject.toml`
- `README.md`
- `src/lander_sim/__main__.py`
- `src/lander_sim/dynamics/state.py`
- `src/lander_sim/dynamics/parameters.py`
- `src/lander_sim/utils/config_io.py`

**Work**
- Create package skeleton and entry point.
- Define typed config/state dataclasses.
- Add preset/config schema versioning to avoid brittle save files later.

### Phase 2 — Dynamics core
**Files**
- `src/lander_sim/dynamics/vehicle_model.py`
- `src/lander_sim/dynamics/integrators.py`
- `src/lander_sim/dynamics/disturbances.py`
- `src/lander_sim/simulation/history.py`
- `src/lander_sim/simulation/runner.py`

**Work**
- Implement explicit nonlinear planar equations.
- Add RK4 default and Euler debug integrator.
- Add clamps, touchdown logic, event logging, and deterministic run history capture.

### Phase 3 — Guidance and controllers
**Files**
- `src/lander_sim/control/guidance.py`
- `src/lander_sim/control/pid_controller.py`
- `src/lander_sim/dynamics/linearization.py`
- `src/lander_sim/control/state_space_controller.py`
- `src/lander_sim/control/actuator_allocator.py`
- `src/lander_sim/simulation/scenarios.py`

**Work**
- Implement mission targets / piecewise segments.
- Implement cascaded PID with explicit loop comments, anti-windup, derivative filtering, and saturation.
- Implement hover trim + continuous-time linearization + discrete conversion at control dt.
- Implement LQR/direct-gain state feedback and actuator allocation modes.

### Phase 4 — Desktop UI MVP
**Files**
- `src/lander_sim/ui/main_window.py`
- `src/lander_sim/ui/theme.py`
- `src/lander_sim/ui/scene_renderer.py`
- `src/lander_sim/ui/playback_controller.py`
- `src/lander_sim/ui/panels/*.py`
- `src/lander_sim/ui/plotting/*.py`

**Work**
- Build main shell with grouped settings, scene view, plots, analytics, and status bar.
- Implement modern dark theme and parameter tooltips.
- Implement live run/playback wiring and run list selection.

### Phase 5 — Comparison workflow and polish
**Files**
- `src/lander_sim/simulation/analytics.py`
- `src/lander_sim/ui/panels/analytics_panel.py`
- `src/lander_sim/ui/plotting/comparison_plot_widget.py`
- `src/lander_sim/data/presets/*.json`

**Work**
- Implement analytics summary and comparison overlays.
- Add shipped presets and reset/re-run workflow.
- Add plot export and CSV export only if the MVP is already stable.

### Phase 6 — Verification and documentation
**Files**
- `tests/*.py`
- `README.md`

**Work**
- Add targeted automated tests and offscreen UI smoke test.
- Document model assumptions, simplifications, and local run instructions.

## 8) Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| UI and sim loop become tightly coupled | Hard-to-maintain code, stuttery UI | Keep a pure headless simulation runner and signal-only UI bridge |
| State-space control becomes mathematically opaque | Users distrust controller comparison | Display state/input definitions, trim point, `A/B`, `Ad/Bd`, `Q/R`, `K`, and poles in UI |
| Comparison runs become non-reproducible | Weak tuning workflow | Persist run metadata and config snapshots inside every `RunResult` |
| Optional features expand scope too early | MVP slips | Defer estimators, Monte Carlo, sweep helpers, and video export until after MVP acceptance |
| Future higher-fidelity work is blocked by current abstractions | Rewrite risk | Keep plant, actuator, guidance, and analytics interfaces separate and typed |

## 9) Verification Plan

See `.omx/plans/test-spec-2d-rocket-lander-sim.md` for the detailed test specification.

The execution handoff is complete only when:
- unit and integration tests pass,
- the UI smoke launch succeeds,
- the stable hover and state-space hover presets run end-to-end,
- one comparison workflow produces named overlaid runs,
- README engineering notes document model assumptions and simplifications.

## 10) Available-Agent-Types Roster

- `architect` — boundaries, extensibility, interface contracts
- `executor` — primary implementation lanes
- `debugger` — numerical/logic fault isolation
- `test-engineer` — test plan execution and fixture design
- `verifier` — completion evidence and final proof
- `designer` — UI layout and interaction refinement
- `writer` — README, help text, preset descriptions
- `code-reviewer` / `critic` — final review / risk challenge

## 11) Follow-up Staffing Guidance

### Recommended `$ralph` path
Use when a single owner should implement sequentially with frequent verification.

- Lane 1: `executor` (high) — bootstrap + dynamics + controllers
- Lane 2: `executor` (high) — UI shell + plots + scene renderer
- Lane 3: `test-engineer` (medium) — tests and scenario validation after core passes
- Lane 4: `verifier` (high) — final evidence pass before stop

### Recommended `$team` path
Use when speed matters and parallel lanes are acceptable.

- **Worker A — Core dynamics/control (`executor`, high)**
  - Owns `dynamics/`, `control/`, `simulation/runner.py`, `simulation/history.py`
- **Worker B — UI/visualization (`executor`, high)**
  - Owns `ui/`, theming, renderer, live plots, run list UX
- **Worker C — Presets/analytics/tests (`test-engineer`, medium)**
  - Owns `simulation/analytics.py`, `data/presets/`, `tests/`, README verification notes
- **Leader / follow-up reviewer (`verifier`, high)**
  - Integrates, runs acceptance checks, confirms comparison workflow, and verifies documentation

## 12) Launch Hints

### Ralph handoff
```text
$ralph Implement .omx/plans/prd-2d-rocket-lander-sim.md and .omx/plans/test-spec-2d-rocket-lander-sim.md. Use the recommended pure-Python PySide6 + pyqtgraph stack and verify against the documented acceptance criteria.
```

### Team handoff
```text
$team Build the app described in .omx/plans/prd-2d-rocket-lander-sim.md using .omx/plans/test-spec-2d-rocket-lander-sim.md as the verification contract. Staff lanes for (A) dynamics/control, (B) UI/visualization, (C) presets/analytics/tests, then close with a verifier pass.
```

## 13) Team Verification Path

Before team shutdown:
1. Worker A proves nonlinear plant, linearization, and controller tests pass.
2. Worker B proves the UI launches and the scene/plots update on a sample run.
3. Worker C proves presets, analytics, and comparison overlays work and documents any residual gaps.
4. The leader/verifier runs the full acceptance checklist from the test spec.
5. If any lane cannot prove its criteria, return to fix loop before handoff completion.

After team shutdown, Ralph/final verifier confirms:
- the app launches locally,
- stable hover and state-space hover presets both run,
- at least one PID-vs-state-space comparison overlay is visible,
- README assumptions match the implemented simplifications.

## 14) Assumptions and Simplifications

- MVP remains 2D planar only.
- Hover linearization is nominal and only locally valid.
- The first version uses a simple ground plane and touchdown classification, not a detailed contact model.
- No estimator/Kalman, Monte Carlo sweep engine, or video export is required for MVP completion.
- The simulation/control core must remain UI-agnostic even though the first UI is Qt-only.

## 15) Local Run Guidance

After implementation:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m lander_sim
```

## 16) Review Changelog

- Added an explicit simulation thread/data-flow boundary so UI and plant remain decoupled.
- Clarified that state-space control uses visible continuous-time linearization plus discrete conversion at control dt.
- Added allocator ownership for gimbal/RCS/hybrid mapping to keep actuator comparisons honest.
- Added config schema/versioning and immutable run metadata for reproducibility.
- Added agent roster, staffing guidance, launch hints, and team verification path for execution handoff.
