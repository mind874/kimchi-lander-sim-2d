import React from 'react';
import ControllerPanel from '../features/controller-panel/ControllerPanel.jsx';
import ControllerInspectorPanel from '../features/inspector/ControllerInspectorPanel.jsx';
import MissionPanel from '../features/mission-panel/MissionPanel.jsx';
import PresetPanel from '../features/preset-panel/PresetPanel.jsx';
import RunBankPanel from '../features/run-bank/RunBankPanel.jsx';
import StatusFooter from '../features/workspace/StatusFooter.jsx';
import WorkspaceHeader from '../features/workspace/WorkspaceHeader.jsx';
import LineChart from '../components/LineChart.jsx';
import MetricStrip from '../components/MetricStrip.jsx';
import SceneView from '../components/SceneView.jsx';
import { useLanderDesktop } from './useLanderDesktop.js';

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

export default function AppShell() {
  const {
    presets,
    config,
    selectedPreset,
    savedRuns,
    currentEntry,
    currentRun,
    overlayRuns,
    sampleIndex,
    playing,
    busy,
    status,
    error,
    setSelectedPreset,
    setSampleIndex,
    setPlaying,
    loadPreset,
    executeRun,
    handleImportConfig,
    handleExportConfig,
    updateConfig,
    toggleRunSelection,
    focusRun,
  } = useLanderDesktop();

  if (!config) {
    return <div className="boot-screen">Loading the Electron bridge and preset library…</div>;
  }

  return (
    <div className="app-shell overhaul-shell">
      <aside className="sidebar overhaul-sidebar">
        <div className="brand-block card mission-brand">
          <div className="eyebrow">React / Electron primary cockpit</div>
          <h1>Kimchi Lander Sim 2D</h1>
          <p>
            A denser, flight-test-first workstation built around the same Python lander core.
            Configure, run, compare, and inspect control laws without falling back to a PySide shell.
          </p>
          <div className="brand-pills">
            <span>Python authority</span>
            <span>Electron shell</span>
            <span>React renderer</span>
          </div>
        </div>
        <PresetPanel
          presets={presets}
          selectedPreset={selectedPreset}
          onSelectPreset={setSelectedPreset}
          onLoadPreset={loadPreset}
          onImportConfig={handleImportConfig}
          onExportConfig={handleExportConfig}
        />
        <MissionPanel config={config} updateConfig={updateConfig} />
        <ControllerPanel config={config} updateConfig={updateConfig} />
      </aside>

      <main className="workspace overhaul-workspace">
        <WorkspaceHeader
          config={config}
          busy={busy}
          playing={playing}
          onRun={executeRun}
          onTogglePlayback={() => setPlaying((value) => !value)}
          onResetPlayback={() => {
            setPlaying(false);
            setSampleIndex(0);
          }}
        />

        {error ? <div className="error-banner card">{error}</div> : null}
        <MetricStrip analytics={currentRun?.analytics} />

        <div className="analysis-grid">
          <div className="scene-column">
            <SceneView run={currentRun} sampleIndex={sampleIndex} />
            <section className="scrubber-shell card">
              <div className="section-heading compact">
                <div>
                  <div className="eyebrow">Playback</div>
                  <h3>Recorded sample timeline</h3>
                  <p>Scrub through the nonlinear simulation history and compare command/response timing.</p>
                </div>
                <div className="scene-meta">sample {currentRun ? sampleIndex + 1 : 0}/{currentRun?.samples?.length ?? 0}</div>
              </div>
              <input
                type="range"
                min="0"
                max={Math.max((currentRun?.samples?.length ?? 1) - 1, 0)}
                value={sampleIndex}
                onChange={(event) => {
                  setSampleIndex(Number(event.target.value));
                  setPlaying(false);
                }}
                disabled={!currentRun}
              />
            </section>
          </div>

          <div className="inspector-column">
            <RunBankPanel
              savedRuns={savedRuns}
              currentRunId={currentEntry?.id}
              selectedRunIds={overlayRuns.filter((entry) => entry.id !== currentEntry?.id).map((entry) => entry.id)}
              onToggleRun={toggleRunSelection}
              onFocusRun={focusRun}
            />
            <ControllerInspectorPanel controllerDetails={currentEntry?.controllerDetails} currentRun={currentRun} />
          </div>
        </div>

        <div className="chart-grid overhaul-chart-grid">
          <LineChart title="Position" subtitle="World-frame x/z displacement across retained runs" runs={overlayRuns} series={SERIES.position} />
          <LineChart title="Velocity" subtitle="vx/vz response and translation quality" runs={overlayRuns} series={SERIES.velocity} />
          <LineChart title="Attitude / mass" subtitle="pitch history, mass depletion, and trim authority" runs={overlayRuns} series={SERIES.attitude} />
          <LineChart title="Commands" subtitle="throttle, gimbal, and RCS effort over time" runs={overlayRuns} series={SERIES.command} />
        </div>

        <StatusFooter status={status} />
      </main>
    </div>
  );
}
