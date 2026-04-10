from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from scipy.linalg import solve_discrete_are

from lander_sim.control.guidance import GuidanceTarget
from lander_sim.dynamics.linearization import HoverLinearization, continuous_hover_linearization
from lander_sim.dynamics.parameters import VehicleParameters
from lander_sim.dynamics.state import AbstractControlCommand, LanderState


@dataclass(slots=True, frozen=True)
class StateSpaceConfig:
    q_diagonal: tuple[float, ...] = (8.0, 12.0, 3.0, 4.0, 40.0, 10.0)
    r_diagonal: tuple[float, ...] = (0.08, 0.4)
    gain_matrix: tuple[tuple[float, ...], ...] | None = None
    max_delta_thrust: float = 8_000.0
    max_pitch_torque: float = 6_000.0

    def q_matrix(self) -> npt.NDArray[np.float64]:
        return np.diag(np.asarray(self.q_diagonal, dtype=float))

    def r_matrix(self) -> npt.NDArray[np.float64]:
        return np.diag(np.asarray(self.r_diagonal, dtype=float))

    def gain_matrix_array(self) -> npt.NDArray[np.float64] | None:
        if self.gain_matrix is None:
            return None
        return np.asarray(self.gain_matrix, dtype=float)


@dataclass(slots=True, frozen=True)
class StateSpaceDesign:
    linearization: HoverLinearization
    K: npt.NDArray[np.float64]
    closed_loop_poles: npt.NDArray[np.complex128]


class StateSpaceController:
    def __init__(self, vehicle: VehicleParameters, control_dt: float, config: StateSpaceConfig | None = None):
        self.vehicle = vehicle
        self.control_dt = control_dt
        self.config = config or StateSpaceConfig()
        self.design = self._build_design()

    @property
    def A(self) -> npt.NDArray[np.float64]:
        return self.design.linearization.A

    @property
    def B(self) -> npt.NDArray[np.float64]:
        return self.design.linearization.B

    @property
    def Ad(self) -> npt.NDArray[np.float64]:
        return self.design.linearization.Ad

    @property
    def Bd(self) -> npt.NDArray[np.float64]:
        return self.design.linearization.Bd

    @property
    def K(self) -> npt.NDArray[np.float64]:
        return self.design.K

    @property
    def closed_loop_poles(self) -> npt.NDArray[np.complex128]:
        return self.design.closed_loop_poles

    @property
    def state_labels(self) -> tuple[str, ...]:
        return self.design.linearization.state_labels

    @property
    def input_labels(self) -> tuple[str, ...]:
        return self.design.linearization.input_labels

    def _build_design(self) -> StateSpaceDesign:
        linearization = continuous_hover_linearization(self.vehicle, dt=self.control_dt)
        direct_gain = self.config.gain_matrix_array()
        if direct_gain is None:
            P = solve_discrete_are(linearization.Ad, linearization.Bd, self.config.q_matrix(), self.config.r_matrix())
            rhs = linearization.Bd.T @ P @ linearization.Ad
            lhs = linearization.Bd.T @ P @ linearization.Bd + self.config.r_matrix()
            K = np.linalg.solve(lhs, rhs)
        else:
            K = direct_gain
        poles = np.linalg.eigvals(linearization.Ad - linearization.Bd @ K)
        return StateSpaceDesign(linearization=linearization, K=K, closed_loop_poles=poles)

    def state_error(self, state: LanderState, target: GuidanceTarget) -> npt.NDArray[np.float64]:
        return np.asarray(
            [
                state.x - target.x,
                state.z - target.z,
                state.vx - target.vx,
                state.vz - target.vz,
                state.theta - target.theta,
                state.omega - target.omega,
            ],
            dtype=float,
        )

    def step(self, state: LanderState, target: GuidanceTarget) -> AbstractControlCommand:
        error = self.state_error(state, target)
        control_delta = -self.K @ error
        delta_thrust = min(max(float(control_delta[0]), -self.config.max_delta_thrust), self.config.max_delta_thrust)
        pitch_torque = min(max(float(control_delta[1]), -self.config.max_pitch_torque), self.config.max_pitch_torque)
        target_thrust = self.design.linearization.trim_input[0] + delta_thrust
        debug = {
            "delta_thrust": delta_thrust,
            "pitch_torque": pitch_torque,
            "pole_real_max": float(np.max(np.real(self.closed_loop_poles))),
        }
        return AbstractControlCommand(target_thrust=target_thrust, pitch_torque=pitch_torque, source="state_space", debug=debug)
