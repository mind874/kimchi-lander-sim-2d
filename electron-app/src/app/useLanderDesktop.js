import { useEffect, useMemo, useState } from 'react';
import { exportConfig, getPreset, importConfig, listPresets, runSimulation } from '../shared/bridge/landerClient.js';
import { setAtPath } from '../shared/utils/configState.js';
import { usePlayback } from './usePlayback.js';

function currentEntryFromState(savedRuns, currentRunId) {
  return savedRuns.find((entry) => entry.id === currentRunId) ?? null;
}

export function useLanderDesktop() {
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
        const presetList = await listPresets();
        if (!mounted) return;
        setPresets(presetList);
        const first = presetList[0];
        if (first) {
          const preset = await getPreset(first.file_name);
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
  const overlayRuns = useMemo(
    () => savedRuns.filter((entry) => entry.id === currentRunId || selectedRunIds.includes(entry.id)),
    [savedRuns, currentRunId, selectedRunIds],
  );

  usePlayback({ playing, currentRun, currentEntry, setPlaying, setSampleIndex });

  async function loadPreset(identifier) {
    try {
      const response = await getPreset(identifier);
      setConfig(response.preset);
      setSelectedPreset(response.file_name);
      setStatus(`Loaded preset ${response.preset.preset_name}.`);
      setError('');
    } catch (bridgeError) {
      setError(String(bridgeError.message ?? bridgeError));
    }
  }

  async function executeRun() {
    if (!config) return;
    setBusy(true);
    setError('');
    try {
      const response = await runSimulation(config);
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

  async function handleImportConfig() {
    try {
      const response = await importConfig();
      if (response.canceled) return;
      setConfig(response.payload);
      setSelectedPreset('');
      setStatus(`Imported config from ${response.filePath}.`);
      setError('');
    } catch (bridgeError) {
      setError(String(bridgeError.message ?? bridgeError));
    }
  }

  async function handleExportConfig() {
    if (!config) return;
    try {
      const response = await exportConfig(config);
      if (response.canceled) return;
      setStatus(`Saved config to ${response.filePath}.`);
      setError('');
    } catch (bridgeError) {
      setError(String(bridgeError.message ?? bridgeError));
    }
  }

  function updateConfig(path, value) {
    setConfig((current) => setAtPath(current, path, value));
  }

  function toggleRunSelection(runId) {
    setSelectedRunIds((ids) => (ids.includes(runId) ? ids.filter((id) => id !== runId) : [...ids, runId]));
  }

  function focusRun(runId) {
    setCurrentRunId(runId);
    setSampleIndex(0);
    setPlaying(false);
  }

  return {
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
  };
}
