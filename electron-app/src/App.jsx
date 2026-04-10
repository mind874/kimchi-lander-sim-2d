import React, { useEffect, useMemo, useState } from 'react';
import LineChart from './components/LineChart.jsx';
import MetricStrip from './components/MetricStrip.jsx';
import SceneView from './components/SceneView.jsx';

const SERIES = {
  position: [
    { source: 'state_history', key: 'x', label: 'x', color: '#7ec4ff' },
    { source: 'state_history', key: 'z', label: 'z', color: '#35d0ba' },
  ],
  velocity: [
    { source: 'state_history', key: 'vx', label: 'vx', color: '#ff9f4d' },
    { source: 'state_history', key: 'vz', label: 'vz', color: '#ff5b7f' },
  ],
  attitude: [
    { source: 'state_history', key: 'theta', label: 'theta', color: '#c58cff' },
    { source: 'state_history', key: 'mass', label: 'mass', color: '#d6f06e' },
  ],
  command: [
    { source: 'command_history', key: 'throttle', label: 'throttle', color: '#89c5ff' },
    { source: 'command_history', key: 'gimbal', label: 'gimbal', color: '#ffd166' },
    { source: 'command_history', key: 'rcs_pitch', label: 'rcs', color: '#ff7b72' },
  ],
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function setAtPath(root, path, value) {
  const next = clone(root);
  let cursor = next;
  for (let index = 0; index < path.length - 1; index += 1) {
    cursor = cursor[path[index]];
  }
  cursor[path[path.length - 1]] = value;
  return next;
}

function formatMatrix(label, matrix) {
  if (!matrix) return `${label}: unavailable`;
  const rows = Array.isArray(matrix) ? matrix : [matrix];
  return `${label}\n${rows.map((row) => (Array.isArray(row) ? row : [row]).map((value) => Number(value).toFixed(3)).join('  ')).join('\n')}`;
}

function currentEntryFromState(savedRuns, currentRunId) {
  return savedRuns.find((entry) => entry.id === currentRunId) ?? null;
}

function safeBridge() {
  if (!window.landerBridge) {
    throw new Error('Electron bridge unavailable. Run this UI inside the Electron shell.');
  }
  return window.landerBridge;
}

export default function App() {
  const [presets, setPresets] = useState([]);
  const [config, setConfig] = useState(null);
  const [selectedPreset, setSelectedPreset] = useState('');
  const [savedRuns, setSavedRuns] = useState([]);
  const [currentRunId, setCurrentRunId] = useState(null);
  const [selectedRunIds, setSelectedRunIds] = useState([]);
  const [sampleIndex, setSampleIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('Ready. Load a preset or import a config.');
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    async function bootstrap() {
      try {
        const bridge = safeBridge();
        const response = await bridge.listPresets();
        if (!mounted) return;
        setPresets(response.presets ?? []);
        const first = response.presets?.[0];
        if (first) {
          const preset = await bridge.getPreset(first.file_name);
          if (!mounted) return;
          setConfig(preset.preset);
          setSelectedPreset(first.file_name);
          setStatus(`Loaded ${preset.preset.preset_name}.`);
        }
      } catch (bridgeError) {
        if (!mounted) return;
        setError(String(bridgeError.message ?? bridgeError));
      }
    }
    bootstrap();
    return () => {
      mounted = false;
    };
  }, []);

  const currentEntry = useMemo(() => currentEntryFromState(savedRuns, currentRunId), [savedRuns, currentRunId]);
  const currentRun = currentEntry?.run ?? null;
  const controllerDetails = currentEntry?.controllerDetails ?? null;
  const overlayRuns = useMemo(() => savedRuns.filter((entry) => entry.id === currentRunId || selectedRunIds.includes(entry.id)), [savedRuns, currentRunId, selectedRunIds]);

  useEffect(() => {
    if (!playing || !currentRun?.samples?.length) return undefined;
    const intervalMs = Math.max(16, Math.round((currentEntry.config.simulation.dt_s * 1000) / Math.max(currentEntry.config.simulation.playback_speed ?? 1, 0.1)));
    const timer = window.setInterval(() => {
      setSampleIndex((index) => {
        const next = index + 1;
        if (next >= currentRun.samples.length) {
          setPlaying(false);
          return currentRun.samples.length - 1;
        }
        return next;
      });
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [playing, currentRun, currentEntry]);

  async function loadPreset(identifier) {
    try {
      const bridge = safeBridge();
      const response = await bridge.getPreset(identifier);
      setConfig(response.preset);
      setSelectedPreset(response.file_name);
      setStatus(`Loaded preset ${response.preset.preset_name}.`);
      setError('');
    } catch (bridgeError) {
      setError(String(bridgeError.message ?? bridgeError));
    }
  }

  async function runSimulation() {
    if (!config) return;
    setBusy(true);
    setError('');
    try {
      const bridge = safeBridge();
      const response = await bridge.runSimulation(config);
      const timestamp = new Date().toISOString().slice(11, 19);
      const entry = {
        id: `${response.run.run_name}-${Date.now()}`,
        label: `${response.run.preset_name} · ${response.run.controller_mode} · ${timestamp}`,
        run: response.run,
        controllerDetails: response.controller_details,
        config: response.config,
      };
      setSavedRuns((runs) => [...runs, entry]);
      setCurrentRunId(entry.id);
      setSelectedRunIds((runs) => Array.from(new Set([...runs, entry.id])).filter((id) => id !== entry.id));
      setSampleIndex(0);
      setPlaying(true);
      setStatus(`Completed ${response.run.run_name}. Final error ${response.run.analytics.final_position_error_m.toFixed(3)} m.`);
    } catch (bridgeError) {
      setError(String(bridgeError.message ?? bridgeError));
    } finally {
      setBusy(false);
    }
  }

  async function importConfig() {
    try {
      const bridge = safeBridge();
      const response = await bridge.loadConfig();
      if (response.canceled) return;
      setConfig(response.payload);
      setSelectedPreset('');
      setStatus(`Imported config from ${response.filePath}.`);
      setError('');
    } catch (bridgeError) {
      setError(String(bridgeError.message ?? bridgeError));
    }
  }

  async function exportConfig() {
    if (!config) return;
    try {
      const bridge = safeBridge();
      const response = await bridge.saveConfig(config);
      if (response.canceled) return;
      setStatus(`Saved config to ${response.filePath}.`);
      setError('');
    } catch (bridgeError) {
      setError(String(bridgeError.message ?? bridgeError));
    }
  }

  function update(path, value) {
    setConfig((current) => setAtPath(current, path, value));
  }

  function toggleRunSelection(runId) {
    setSelectedRunIds((ids) => (ids.includes(runId) ? ids.filter((id) => id !== runId) : [...ids, runId]));
  }

  if (!config) {
    return <div className="boot-screen">Loading the Electron bridge and preset library…</div>;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block card">
          <div className="eyebrow">Electron / React front-end</div>
          <h1>Kimchi Lander Sim 2D</h1>
          <p>
            Industrial cockpit styling over the same Python simulation core. Tune parameters, retain runs,
            and compare PID versus state-space behavior without leaving the desktop shell.
          </p>
        </div>

        <section className="panel card">
          <div className="section-heading compact">
            <div>
              <h3>Preset / config</h3>
              <p>Load built-in missions or import/export JSON configs.</p>
            </div>
          </div>
          <label>
            Preset
            <select value={selectedPreset} onChange={(event) => setSelectedPreset(event.target.value)}>
              <option value="">Custom / imported</option>
              {presets.map((preset) => (
                <option key={preset.file_name} value={preset.file_name}>{preset.preset_name}</option>
              ))}
            </select>
          </label>
          <div className="button-row">
            <button onClick={() => loadPreset(selectedPreset)} disabled={!selectedPreset}>Load preset</button>
            <button className="ghost" onClick={importConfig}>Import JSON</button>
            <button className="ghost" onClick={exportConfig}>Export JSON</button>
          </div>
        </section>

        <section className="panel card">
          <div className="section-heading compact">
            <div>
              <h3>Mode / mission</h3>
              <p>Controller architecture, allocation, and top-level mission targets.</p>
            </div>
          </div>
          <div className="grid two-col">
            <label>
              Controller
              <select value={config.controller_mode} onChange={(event) => update(['controller_mode'], event.target.value)}>
                <option value="pid">Cascaded PID</option>
                <option value="state_space">State-space / LQR</option>
                <option value="open_loop">Open loop</option>
              </select>
            </label>
            <label>
              Allocator
              <select value={config.allocator_mode ?? 'hybrid'} onChange={(event) => update(['allocator_mode'], event.target.value)}>
                <option value="hybrid">Hybrid</option>
                <option value="gimbal_only">Gimbal only</option>
                <option value="rcs_only">RCS only</option>
              </select>
            </label>
            <label>
              dt [s]
              <input type="number" step="0.005" value={config.simulation.dt_s} onChange={(event) => update(['simulation', 'dt_s'], Number(event.target.value))} />
            </label>
            <label>
              Duration [s]
              <input type="number" step="0.5" value={config.simulation.duration_s} onChange={(event) => update(['simulation', 'duration_s'], Number(event.target.value))} />
            </label>
            <label>
              Target x [m]
              <input type="number" step="0.5" value={config.target.x_m} onChange={(event) => update(['target', 'x_m'], Number(event.target.value))} />
            </label>
            <label>
              Target z [m]
              <input type="number" step="0.5" value={config.target.z_m} onChange={(event) => update(['target', 'z_m'], Number(event.target.value))} />
            </label>
            <label>
              Initial x [m]
              <input type="number" step="0.5" value={config.initial_state.x_m} onChange={(event) => update(['initial_state', 'x_m'], Number(event.target.value))} />
            </label>
            <label>
              Initial z [m]
              <input type="number" step="0.5" value={config.initial_state.z_m} onChange={(event) => update(['initial_state', 'z_m'], Number(event.target.value))} />
            </label>
            <label>
              Initial theta [deg]
              <input type="number" step="0.5" value={config.initial_state.theta_deg} onChange={(event) => update(['initial_state', 'theta_deg'], Number(event.target.value))} />
            </label>
            <label>
              Playback speed
              <input type="number" step="0.1" value={config.simulation.playback_speed ?? 1} onChange={(event) => update(['simulation', 'playback_speed'], Number(event.target.value))} />
            </label>
          </div>
        </section>

        <section className="panel card">
          <div className="section-heading compact">
            <div>
              <h3>{config.controller_mode === 'state_space' ? 'LQR weights' : 'PID gains'}</h3>
              <p>{config.controller_mode === 'state_space' ? 'Hover-linearized state penalties and control weights.' : 'Direct loop gains exposed without hiding the control structure.'}</p>
            </div>
          </div>
          {config.controller_mode === 'state_space' ? (
            <div className="grid two-col dense-grid">
              {config.controller.state_space.q_diagonal.map((value, index) => (
                <label key={`q-${index}`}>
                  Q[{index + 1}]
                  <input type="number" step="0.5" value={value} onChange={(event) => update(['controller', 'state_space', 'q_diagonal', index], Number(event.target.value))} />
                </label>
              ))}
              {config.controller.state_space.r_diagonal.map((value, index) => (
                <label key={`r-${index}`}>
                  R[{index + 1}]
                  <input type="number" step="0.05" value={value} onChange={(event) => update(['controller', 'state_space', 'r_diagonal', index], Number(event.target.value))} />
                </label>
              ))}
            </div>
          ) : (
            <div className="grid two-col dense-grid">
              {[
                ['Altitude Kp', ['controller', 'pid', 'altitude', 'kp']],
                ['Altitude Ki', ['controller', 'pid', 'altitude', 'ki']],
                ['Altitude Kd', ['controller', 'pid', 'altitude', 'kd']],
                ['Lateral Kp', ['controller', 'pid', 'lateral', 'kp']],
                ['Lateral Ki', ['controller', 'pid', 'lateral', 'ki']],
                ['Lateral Kd', ['controller', 'pid', 'lateral', 'kd']],
                ['Attitude Kp', ['controller', 'pid', 'attitude', 'kp']],
                ['Attitude Ki', ['controller', 'pid', 'attitude', 'ki']],
                ['Attitude Kd', ['controller', 'pid', 'attitude', 'kd']],
              ].map(([label, path]) => (
                <label key={label}>
                  {label}
                  <input type="number" step="0.05" value={path.reduce((cursor, key) => cursor[key], config)} onChange={(event) => update(path, Number(event.target.value))} />
                </label>
              ))}
            </div>
          )}
        </section>

        <section className="panel card run-bank">
          <div className="section-heading compact">
            <div>
              <h3>Run bank</h3>
              <p>Select retained runs to overlay them on the charts.</p>
            </div>
          </div>
          <div className="run-list">
            {savedRuns.map((entry) => (
              <label key={entry.id} className={`run-item ${entry.id === currentRunId ? 'current' : ''}`}>
                <input
                  type="checkbox"
                  checked={entry.id === currentRunId || selectedRunIds.includes(entry.id)}
                  onChange={() => entry.id === currentRunId ? setCurrentRunId(entry.id) : toggleRunSelection(entry.id)}
                />
                <span>
                  <strong>{entry.run.preset_name}</strong>
                  <small>{entry.label}</small>
                </span>
                <button className="text-button" onClick={() => { setCurrentRunId(entry.id); setSampleIndex(0); setPlaying(false); }}>
                  Focus
                </button>
              </label>
            ))}
            {!savedRuns.length && <div className="empty-inline">No runs retained yet.</div>}
          </div>
        </section>
      </aside>

      <main className="workspace">
        <header className="workspace-header card">
          <div>
            <div className="eyebrow">Status</div>
            <h2>{config.preset_name}</h2>
            <p>{config.description}</p>
          </div>
          <div className="header-actions">
            <button className="primary" onClick={runSimulation} disabled={busy}>{busy ? 'Running…' : 'Run simulation'}</button>
            <button onClick={() => setPlaying((value) => !value)} disabled={!currentRun}>{playing ? 'Pause' : 'Play'}</button>
            <button onClick={() => { setPlaying(false); setSampleIndex(0); }} disabled={!currentRun}>Reset view</button>
          </div>
        </header>

        {error ? <div className="error-banner card">{error}</div> : null}
        <MetricStrip analytics={currentRun?.analytics} />

        <div className="hero-grid">
          <SceneView run={currentRun} sampleIndex={sampleIndex} />
          <section className="matrix-shell card">
            <div className="section-heading">
              <div>
                <h3>Controller transparency</h3>
                <p>Live controller metadata exposed from the Python core.</p>
              </div>
              <div className="scene-meta">{controllerDetails?.kind ?? '—'}</div>
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
          </section>
        </div>

        <div className="scrubber-shell card">
          <div className="section-heading compact">
            <div>
              <h3>Playback</h3>
              <p>Scrub through the recorded sample history.</p>
            </div>
            <div className="scene-meta">sample {currentRun ? sampleIndex + 1 : 0}/{currentRun?.samples?.length ?? 0}</div>
          </div>
          <input
            type="range"
            min="0"
            max={Math.max((currentRun?.samples?.length ?? 1) - 1, 0)}
            value={sampleIndex}
            onChange={(event) => { setSampleIndex(Number(event.target.value)); setPlaying(false); }}
            disabled={!currentRun}
          />
        </div>

        <div className="chart-grid">
          <LineChart title="Position" subtitle="x/z world-frame displacement" runs={overlayRuns} series={SERIES.position} />
          <LineChart title="Velocity" subtitle="vx/vz response across retained runs" runs={overlayRuns} series={SERIES.velocity} />
          <LineChart title="Attitude / mass" subtitle="pitch and mass history" runs={overlayRuns} series={SERIES.attitude} />
          <LineChart title="Commands" subtitle="throttle, gimbal, and RCS effort" runs={overlayRuns} series={SERIES.command} />
        </div>

        <footer className="footer-strip">
          <span>{status}</span>
          <span>Electron ↔ Python bridge running against the same lander core used by the PySide desktop app.</span>
        </footer>
      </main>
    </div>
  );
}
