import React from 'react';

export default function MissionPanel({ config, updateConfig }) {
  return (
    <section className="dock-panel card">
      <div className="section-heading compact">
        <div>
          <div className="eyebrow">Mission</div>
          <h3>Scenario + vehicle</h3>
          <p>Flight mode, allocator, timebase, target, and initial conditions.</p>
        </div>
      </div>
      <div className="grid two-col dense-grid">
        <label>
          Controller
          <select value={config.controller_mode} onChange={(event) => updateConfig(['controller_mode'], event.target.value)}>
            <option value="pid">Cascaded PID</option>
            <option value="state_space">State-space / LQR</option>
            <option value="open_loop">Open loop</option>
          </select>
        </label>
        <label>
          Allocator
          <select value={config.allocator_mode ?? 'hybrid'} onChange={(event) => updateConfig(['allocator_mode'], event.target.value)}>
            <option value="hybrid">Hybrid</option>
            <option value="gimbal_only">Gimbal only</option>
            <option value="rcs_only">RCS only</option>
          </select>
        </label>
        <label>
          dt [s]
          <input type="number" step="0.005" value={config.simulation.dt_s} onChange={(event) => updateConfig(['simulation', 'dt_s'], Number(event.target.value))} />
        </label>
        <label>
          Duration [s]
          <input type="number" step="0.5" value={config.simulation.duration_s} onChange={(event) => updateConfig(['simulation', 'duration_s'], Number(event.target.value))} />
        </label>
        <label>
          Dry mass [kg]
          <input type="number" step="10" value={config.vehicle.dry_mass_kg} onChange={(event) => updateConfig(['vehicle', 'dry_mass_kg'], Number(event.target.value))} />
        </label>
        <label>
          Initial mass [kg]
          <input type="number" step="10" value={config.vehicle.initial_mass_kg} onChange={(event) => updateConfig(['vehicle', 'initial_mass_kg'], Number(event.target.value))} />
        </label>
        <label>
          Max thrust [N]
          <input type="number" step="100" value={config.vehicle.max_thrust_n} onChange={(event) => updateConfig(['vehicle', 'max_thrust_n'], Number(event.target.value))} />
        </label>
        <label>
          Iyy [kg m²]
          <input type="number" step="10" value={config.vehicle.inertia_kg_m2} onChange={(event) => updateConfig(['vehicle', 'inertia_kg_m2'], Number(event.target.value))} />
        </label>
        <label>
          Target x [m]
          <input type="number" step="0.5" value={config.target.x_m} onChange={(event) => updateConfig(['target', 'x_m'], Number(event.target.value))} />
        </label>
        <label>
          Target z [m]
          <input type="number" step="0.5" value={config.target.z_m} onChange={(event) => updateConfig(['target', 'z_m'], Number(event.target.value))} />
        </label>
        <label>
          Initial x [m]
          <input type="number" step="0.5" value={config.initial_state.x_m} onChange={(event) => updateConfig(['initial_state', 'x_m'], Number(event.target.value))} />
        </label>
        <label>
          Initial z [m]
          <input type="number" step="0.5" value={config.initial_state.z_m} onChange={(event) => updateConfig(['initial_state', 'z_m'], Number(event.target.value))} />
        </label>
        <label>
          Initial theta [deg]
          <input type="number" step="0.5" value={config.initial_state.theta_deg} onChange={(event) => updateConfig(['initial_state', 'theta_deg'], Number(event.target.value))} />
        </label>
        <label>
          Initial omega [deg/s]
          <input type="number" step="0.5" value={config.initial_state.omega_deg_s} onChange={(event) => updateConfig(['initial_state', 'omega_deg_s'], Number(event.target.value))} />
        </label>
      </div>
      <div className="small-note">All simulation math remains SI/radians internally even though the frontend exposes practical engineering units.</div>
    </section>
  );
}
