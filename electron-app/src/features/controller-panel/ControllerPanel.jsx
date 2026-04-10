import React from 'react';
import { readAtPath } from '../../shared/utils/configState.js';

const PID_FIELDS = [
  ['Altitude Kp', ['controller', 'pid', 'altitude', 'kp']],
  ['Altitude Ki', ['controller', 'pid', 'altitude', 'ki']],
  ['Altitude Kd', ['controller', 'pid', 'altitude', 'kd']],
  ['Lateral Kp', ['controller', 'pid', 'lateral', 'kp']],
  ['Lateral Ki', ['controller', 'pid', 'lateral', 'ki']],
  ['Lateral Kd', ['controller', 'pid', 'lateral', 'kd']],
  ['Attitude Kp', ['controller', 'pid', 'attitude', 'kp']],
  ['Attitude Ki', ['controller', 'pid', 'attitude', 'ki']],
  ['Attitude Kd', ['controller', 'pid', 'attitude', 'kd']],
];

export default function ControllerPanel({ config, updateConfig }) {
  return (
    <section className="dock-panel card">
      <div className="section-heading compact">
        <div>
          <div className="eyebrow">Control law</div>
          <h3>{config.controller_mode === 'state_space' ? 'LQR / state-space' : config.controller_mode === 'open_loop' ? 'Open-loop actuator commands' : 'PID loops'}</h3>
          <p>
            {config.controller_mode === 'state_space'
              ? 'Edit hover-linearized state penalties and control weights.'
              : config.controller_mode === 'open_loop'
                ? 'Direct thrust, gimbal, and RCS command shaping.'
                : 'Edit the explicit cascaded PID loop gains.'}
          </p>
        </div>
      </div>
      {config.controller_mode === 'state_space' ? (
        <div className="grid two-col dense-grid">
          {config.controller.state_space.q_diagonal.map((value, index) => (
            <label key={`q-${index}`}>
              Q[{index + 1}]
              <input type="number" step="0.5" value={value} onChange={(event) => updateConfig(['controller', 'state_space', 'q_diagonal', index], Number(event.target.value))} />
            </label>
          ))}
          {config.controller.state_space.r_diagonal.map((value, index) => (
            <label key={`r-${index}`}>
              R[{index + 1}]
              <input type="number" step="0.05" value={value} onChange={(event) => updateConfig(['controller', 'state_space', 'r_diagonal', index], Number(event.target.value))} />
            </label>
          ))}
        </div>
      ) : config.controller_mode === 'open_loop' ? (
        <div className="grid two-col dense-grid">
          <label>
            Throttle
            <input type="number" step="0.01" value={config.controller.open_loop?.throttle ?? 0.65} onChange={(event) => updateConfig(['controller', 'open_loop', 'throttle'], Number(event.target.value))} />
          </label>
          <label>
            Gimbal [deg]
            <input type="number" step="0.1" value={config.controller.open_loop?.gimbal_deg ?? 0.0} onChange={(event) => updateConfig(['controller', 'open_loop', 'gimbal_deg'], Number(event.target.value))} />
          </label>
          <label>
            RCS torque [N m]
            <input type="number" step="10" value={config.controller.open_loop?.rcs_torque_n_m ?? 0.0} onChange={(event) => updateConfig(['controller', 'open_loop', 'rcs_torque_n_m'], Number(event.target.value))} />
          </label>
        </div>
      ) : (
        <div className="grid two-col dense-grid">
          {PID_FIELDS.map(([label, path]) => (
            <label key={label}>
              {label}
              <input type="number" step="0.05" value={readAtPath(config, path)} onChange={(event) => updateConfig(path, Number(event.target.value))} />
            </label>
          ))}
        </div>
      )}
      <div className="small-note">The JavaScript shell edits configuration only; every simulation run still executes through the Python core.</div>
    </section>
  );
}
