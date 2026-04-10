import React from 'react';

const METRICS = [
  ['Final error', (analytics) => `${analytics?.final_position_error_m?.toFixed?.(3) ?? '—'} m`],
  ['Touchdown velocity', (analytics) => analytics?.touchdown_velocity_mps == null ? '—' : `${analytics.touchdown_velocity_mps.toFixed(3)} m/s`],
  ['Peak angle', (analytics) => `${analytics?.peak_angle_deg?.toFixed?.(3) ?? '—'} deg`],
  ['Fuel used', (analytics) => `${analytics?.fuel_consumed_kg?.toFixed?.(3) ?? '—'} kg`],
  ['RCS pulses', (analytics) => `${analytics?.rcs_pulse_count ?? '—'}`],
  ['Saturation', (analytics) => `${((analytics?.saturation_fraction ?? 0) * 100).toFixed(1)} %`],
];

export default function MetricStrip({ analytics }) {
  return (
    <div className="metrics-grid">
      {METRICS.map(([label, render]) => (
        <article key={label} className="metric-card card">
          <span>{label}</span>
          <strong>{render(analytics)}</strong>
        </article>
      ))}
    </div>
  );
}
