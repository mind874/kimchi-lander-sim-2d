import React from 'react';

export default function RunBankPanel({ savedRuns, currentRunId, selectedRunIds, onToggleRun, onFocusRun }) {
  return (
    <section className="dock-panel card run-bank-panel">
      <div className="section-heading compact">
        <div>
          <div className="eyebrow">Runs</div>
          <h3>Comparison bank</h3>
          <p>Retain multiple runs and overlay them in the analysis deck.</p>
        </div>
      </div>
      <div className="run-list compact-run-list">
        {savedRuns.map((entry) => {
          const selected = entry.id === currentRunId || selectedRunIds.includes(entry.id);
          return (
            <label key={entry.id} className={`run-item ${entry.id === currentRunId ? 'current' : ''}`}>
              <input type="checkbox" checked={selected} onChange={() => onToggleRun(entry.id)} />
              <span>
                <strong>{entry.run.preset_name}</strong>
                <small>{entry.label}</small>
              </span>
              <button className="text-button" onClick={() => onFocusRun(entry.id)}>Focus</button>
            </label>
          );
        })}
        {!savedRuns.length && <div className="empty-inline">No retained runs yet.</div>}
      </div>
    </section>
  );
}
