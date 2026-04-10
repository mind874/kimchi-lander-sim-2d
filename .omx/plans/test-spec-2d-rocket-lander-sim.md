# Test Specification — Desktop-Grade 2D Rocket Lander Engineering Simulator

**Companion PRD:** `.omx/plans/prd-2d-rocket-lander-sim.md`  
**Date:** 2026-04-10

## 1) Verification Goals

Prove that the delivered MVP:

- simulates the requested 2D rigid-body states and forces correctly
- exposes genuine PID and state-space control paths
- supports live tuning, presets, and comparison workflows
- launches as a usable local desktop application
- documents its assumptions honestly

## 2) Test Layers

### A. Unit tests

#### `tests/test_vehicle_model.py`
- Verify gravity-only propagation changes `vz` and `z` with correct sign convention.
- Verify thrust-to-world transform at `theta = 0`, positive pitch, and negative pitch.
- Verify gimbal torque sign and RCS torque sign match geometry definitions.
- Verify mass depletion cannot reduce mass below dry mass.
- Verify touchdown handling prevents continued downward penetration after landing/crash state.

#### `tests/test_integrators.py`
- Verify Euler and RK4 both advance a simple known ODE correctly.
- Verify RK4 converges closer than Euler on the same nonlinear open-loop case at equal `dt`.
- Verify fixed-step history length equals expected sample count.

#### `tests/test_linearization.py`
- Verify hover trim produces `T_hover ≈ m_nominal * g`.
- Verify small perturbation nonlinear response matches `A/B` prediction locally.
- Verify discretization produces stable `Ad/Bd` dimensions for the active control `dt`.

#### `tests/test_pid_controller.py`
- Verify outer-loop commands produce bounded attitude/thrust requests.
- Verify anti-windup prevents integral growth when throttle saturates.
- Verify derivative filtering / rate damping behaves numerically when measurements step.

#### `tests/test_state_space_controller.py`
- Verify LQR or direct-gain path returns the expected gain matrix shape.
- Verify controller exposes state vector, input vector, and closed-loop poles.
- Verify control output saturates cleanly through allocator limits.

#### `tests/test_guidance.py`
- Verify hover target generation, lateral translation target, and hop/land sequence references.
- Verify segment transitions occur at the planned times.

#### `tests/test_analytics.py`
- Verify touchdown velocity, final error, fuel used, and saturation fraction calculations.
- Verify run comparison metadata preserves preset/controller names.

### B. Integration tests

#### Scenario regressions
Run the following scripted scenarios using the real nonlinear plant and controller stack:

1. **Stable hover preset**
   - Controller: PID
   - Pass criteria:
     - no crash
     - final `|x_error| <= 0.5 m`
     - final `|z_error| <= 0.5 m`
     - final `|theta| <= 5 deg`

2. **State-space hover preset**
   - Controller: state-space
   - Pass criteria:
     - no crash
     - final `|x_error| <= 0.5 m`
     - final `|z_error| <= 0.5 m`
     - closed-loop poles are displayed and finite

3. **Poorly tuned PID preset**
   - Controller: PID
   - Pass criteria:
     - run completes without numerical blow-up
     - analytics reflect worse overshoot or settling than the tuned hover preset

4. **Lateral translation preset**
   - Controller: PID and state-space, run separately
   - Pass criteria:
     - both runs are stored
     - comparison overlay shows both traces with unique labels

5. **Landing with mass depletion preset**
   - Controller: chosen preset controller
   - Pass criteria:
     - fuel use is nonzero
     - landing pass/fail is computed
     - touchdown event is present in run history

### C. UI smoke / application tests

#### `tests/test_smoke_ui.py`
- Launch the main window in offscreen/headless-friendly mode.
- Verify the main panels instantiate:
  - settings/tuning container
  - simulation scene widget
  - plot manager
  - analytics panel
  - status bar
- Verify loading a preset updates the bound configuration model.
- Verify run/start and reset actions are connected without raising exceptions.

### D. Manual engineering acceptance checks

1. Launch app locally.
2. Load **Stable hover** preset and run to completion.
3. Load **State-space hover** preset and run to completion.
4. Inspect that:
   - the scene shows body, thrust vector, target marker, and trail
   - plots update during the run
   - analytics panel reports final error, peak angle, and fuel use
5. Run **Lateral translation** for PID and state-space, then compare overlaid plots.
6. Save a config, reload it, and confirm parameter values persist.

## 3) Tooling / Commands

Expected commands after implementation:

```bash
python -m pytest
python -m pytest tests/test_smoke_ui.py
python -m lander_sim
```

## 4) Failure Gates

Execution is **not complete** if any of the following remain true:

- plant math tests fail
- controller tests fail
- hover presets crash or diverge numerically
- state-space mode does not expose its matrices/gains/poles
- comparison overlay cannot retain and label at least two runs
- UI cannot launch in smoke mode
- README omits model assumptions and simplifications

## 5) Evidence to Collect Before Declaring Done

- test command output for unit/integration coverage
- smoke-launch output or a note confirming successful offscreen start
- at least one saved comparison run pair (PID vs state-space)
- README section summarizing:
  - model assumptions
  - intended simplifications
  - future fidelity extensions needed for higher realism
