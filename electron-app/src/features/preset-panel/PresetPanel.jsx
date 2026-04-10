import React from 'react';

export default function PresetPanel({ presets, selectedPreset, onSelectPreset, onLoadPreset, onImportConfig, onExportConfig }) {
  return (
    <section className="dock-panel card">
      <div className="section-heading compact">
        <div>
          <div className="eyebrow">Library</div>
          <h3>Preset / config</h3>
          <p>Load built-in missions or import/export JSON configs.</p>
        </div>
      </div>
      <label>
        Preset
        <select value={selectedPreset} onChange={(event) => onSelectPreset(event.target.value)}>
          <option value="">Custom / imported</option>
          {presets.map((preset) => (
            <option key={preset.file_name} value={preset.file_name}>{preset.preset_name}</option>
          ))}
        </select>
      </label>
      <div className="button-row stacked-row">
        <button onClick={() => onLoadPreset(selectedPreset)} disabled={!selectedPreset}>Load preset</button>
        <button className="ghost" onClick={onImportConfig}>Import JSON</button>
        <button className="ghost" onClick={onExportConfig}>Export JSON</button>
      </div>
      <div className="small-note">Electron is the primary shell. Use presets to compare controller behavior on the same plant.</div>
    </section>
  );
}
