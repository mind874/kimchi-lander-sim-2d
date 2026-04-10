import React from 'react';

function formatMatrix(label, matrix) {
  if (!matrix) return `${label}: unavailable`;
  const rows = Array.isArray(matrix) ? matrix : [matrix];
  return `${label}\n${rows.map((row) => (Array.isArray(row) ? row : [row]).map((value) => Number(value).toFixed(3)).join('  ')).join('\n')}`;
}

function EventList({ events }) {
  if (!events?.length) return <div className="empty-inline">No events recorded.</div>;
  return (
    <div className="event-list">
      {events.slice(-6).map((event, index) => (
        <div key={`${event.name ?? event.kind}-${index}`} className="event-pill">
          <strong>{event.name ?? event.kind}</strong>
          <span>{event.touchdown_velocity_mps != null ? `${event.touchdown_velocity_mps.toFixed(2)} m/s` : event.value ?? ''}</span>
        </div>
      ))}
    </div>
  );
}

export default function ControllerInspectorPanel({ controllerDetails, currentRun }) {
  const analytics = currentRun?.analytics;
  return (
    <section className="inspector-stack">
      <article className="matrix-shell card">
        <div className="section-heading compact">
          <div>
            <div className="eyebrow">Controller transparency</div>
            <h3>{controllerDetails?.kind === 'state_space' ? 'Linear model + poles' : 'Loop structure + gains'}</h3>
            <p>Always sourced from the Python controller implementation.</p>
          </div>
        </div>
        {controllerDetails?.kind === 'state_space' ? (
          <div className="matrix-grid">
            <pre>{formatMatrix('A', controllerDetails.A)}</pre>
            <pre>{formatMatrix('B', controllerDetails.B)}</pre>
            <pre>{formatMatrix('K', controllerDetails.K)}</pre>
            <pre>{`Poles\n${controllerDetails.closed_loop_poles.map((pole) => `${pole.real.toFixed(3)} ${pole.imag >= 0 ? '+' : '-'} ${Math.abs(pole.imag).toFixed(3)}j`).join('\n')}`}</pre>
          </div>
        ) : (
          <pre className="loop-note">{JSON.stringify(controllerDetails ?? { note: 'Run a scenario to populate controller details.' }, null, 2)}</pre>
        )}
      </article>

      <article className="matrix-shell card">
        <div className="section-heading compact">
          <div>
            <div className="eyebrow">Result summary</div>
            <h3>Run analytics + events</h3>
            <p>Failure conditions, landing status, and recent event flags.</p>
          </div>
        </div>
        <div className="analytics-grid">
          <div><span>Run</span><strong>{currentRun?.run_name ?? '—'}</strong></div>
          <div><span>Preset</span><strong>{currentRun?.preset_name ?? '—'}</strong></div>
          <div><span>Final error</span><strong>{analytics ? `${analytics.final_position_error_m.toFixed(3)} m` : '—'}</strong></div>
          <div><span>Peak angle</span><strong>{analytics ? `${analytics.peak_angle_deg.toFixed(3)} deg` : '—'}</strong></div>
          <div><span>Fuel used</span><strong>{analytics ? `${analytics.fuel_consumed_kg.toFixed(3)} kg` : '—'}</strong></div>
          <div><span>Landing pass</span><strong>{analytics ? String(analytics.landing_pass) : '—'}</strong></div>
        </div>
        <EventList events={currentRun?.events} />
      </article>
    </section>
  );
}
