import React from 'react';

function renderCandidates(diagnostics) {
  if (!diagnostics?.pythonCandidates?.length) return 'No Python candidates reported';
  return diagnostics.pythonCandidates.join('\n');
}

export default function StartupDiagnostics({ error, diagnostics, onRetry }) {
  return (
    <div className="boot-screen diagnostics-screen">
      <section className="diagnostics-card card">
        <div className="eyebrow">Startup diagnostics</div>
        <h1>Bridge startup failed</h1>
        <p>
          The React cockpit could not load the Python preset library, so the app stopped before rendering the main workspace.
          Use the details below instead of waiting on a blank loading screen.
        </p>

        <div className="diagnostic-block">
          <span>Observed error</span>
          <strong>{error || 'Unknown bridge failure'}</strong>
        </div>

        <div className="diagnostic-grid">
          <div>
            <span>Repo root</span>
            <pre>{diagnostics?.repoRoot ?? 'Unavailable'}</pre>
          </div>
          <div>
            <span>Python candidates</span>
            <pre>{renderCandidates(diagnostics)}</pre>
          </div>
          <div>
            <span>Bridge probe</span>
            <pre>{diagnostics?.ok ? `OK · ${diagnostics.presetCount ?? 0} presets visible` : diagnostics?.error ?? 'Probe unavailable'}</pre>
          </div>
        </div>

        <div className="button-row stacked-row diagnostics-actions">
          <button className="primary" onClick={onRetry}>Retry bridge bootstrap</button>
        </div>

        <div className="diagnostics-hints">
          <span>Suggested checks</span>
          <pre>{`./scripts/bootstrap.sh\npython -m lander_sim bridge list-presets\nnpm run electron:build`}</pre>
        </div>
      </section>
    </div>
  );
}
