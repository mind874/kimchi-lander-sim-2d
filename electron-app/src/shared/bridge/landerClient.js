function safeBridge() {
  if (!window.landerBridge) {
    throw new Error('Electron bridge unavailable. Run this UI inside the Electron shell.');
  }
  return window.landerBridge;
}

export async function listPresets() {
  const response = await safeBridge().listPresets();
  return response.presets ?? [];
}

export async function getPreset(identifier) {
  return safeBridge().getPreset(identifier);
}

export async function runSimulation(config) {
  return safeBridge().runSimulation(config);
}

export async function diagnostics() {
  return safeBridge().diagnostics();
}

export function reportStartupStatus(payload) {
  return safeBridge().reportStartupStatus(payload);
}

export async function importConfig() {
  return safeBridge().loadConfig();
}

export async function exportConfig(config) {
  return safeBridge().saveConfig(config);
}
