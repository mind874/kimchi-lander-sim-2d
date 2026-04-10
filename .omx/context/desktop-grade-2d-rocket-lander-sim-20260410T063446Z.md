# Context Snapshot — desktop-grade-2d-rocket-lander-sim

## Task statement
Plan a polished local engineering simulation tool for a 2D rocket lander hop vehicle focused on guidance, control, tuning, visualization, and comparison of PID versus state-space control on the same vehicle model.

## Desired outcome
- A grounded MVP-to-polish delivery plan for a desktop application.
- A clear architecture, file tree, implementation phases, verification strategy, and execution handoff artifacts.
- Plan artifacts that can drive follow-on `$ralph` or `$team` execution without re-scoping.

## Known facts / evidence
- Repository root is currently empty aside from OMX runtime metadata under `.omx/`.
- No existing physics, control, or UI code is present yet.
- The request strongly prefers a Python simulation backend and allows either Electron or a Python-native desktop UI; robustness, responsiveness, maintainability, and plotting quality are the primary stack drivers.
- The required MVP includes:
  - 2D rigid-body simulation
  - one clean visualization pane
  - live plots
  - PID mode
  - state-space mode
  - editable parameters
  - presets
  - save/load config
  - at least one comparison workflow
- The user explicitly wants an engineering tool, not a game, and prioritizes numerical clarity, modular code, and extendability toward higher-fidelity future work.

## Constraints
- Use SI units and radians internally.
- Keep simulation logic separate from UI logic.
- Do not hide the plant or controller math behind vague abstractions.
- Support both PID and genuine state-space / full-state feedback control.
- Keep the codebase modular and suitable for growth toward 3D or higher-fidelity dynamics.
- Prefer a UI stack that makes real-time plotting and desktop-grade interaction practical.
- Final user-facing output from planning must include architecture summary, proposed file tree, implementation notes, assumptions/simplifications, and local run instructions.

## Unknowns / open questions
- Whether the first implementation should package as a pure Python desktop app or a hybrid Electron/Python stack.
- Whether optional features like estimator/Kalman filtering, Monte Carlo sweeps, or automated tuning should be included in MVP or deferred.
- Exact choice of plotting/scene toolkit within a Python desktop approach.
- Packaging/distribution expectations beyond local development.

## Likely codebase touchpoints
- `README.md`
- `pyproject.toml`
- `src/lander_sim/dynamics/`
- `src/lander_sim/control/`
- `src/lander_sim/ui/`
- `src/lander_sim/data/presets/`
- `tests/`
