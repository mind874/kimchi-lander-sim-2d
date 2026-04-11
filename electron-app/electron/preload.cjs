const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('landerBridge', {
  listPresets: () => ipcRenderer.invoke('lander:list-presets'),
  getPreset: (identifier) => ipcRenderer.invoke('lander:get-preset', identifier),
  runSimulation: (payload) => ipcRenderer.invoke('lander:run-simulation', payload),
  diagnostics: () => ipcRenderer.invoke('lander:diagnostics'),
  saveConfig: (payload) => ipcRenderer.invoke('lander:save-config', payload),
  loadConfig: () => ipcRenderer.invoke('lander:load-config'),
  reportStartupStatus: (payload) => ipcRenderer.send('lander:startup-status', payload),
});
