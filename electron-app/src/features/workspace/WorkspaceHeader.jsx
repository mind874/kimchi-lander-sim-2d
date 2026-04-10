import React from 'react';

export default function WorkspaceHeader({ config, busy, playing, onRun, onTogglePlayback, onResetPlayback }) {
  return (
    <header className="workspace-header card">
      <div>
        <div className="eyebrow">Primary frontend</div>
        <h2>{config.preset_name}</h2>
        <p>{config.description}</p>
      </div>
      <div className="header-actions">
        <button className="primary" onClick={onRun} disabled={busy}>{busy ? 'Running…' : 'Run simulation'}</button>
        <button onClick={onTogglePlayback}>{playing ? 'Pause' : 'Play'}</button>
        <button onClick={onResetPlayback}>Reset view</button>
      </div>
    </header>
  );
}
