import { app, BrowserWindow, dialog, ipcMain } from 'electron';
import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..', '..');
const smokeMode = process.env.LANDER_ELECTRON_SMOKE === '1';
const smokeTimeoutMs = Number(process.env.LANDER_ELECTRON_SMOKE_TIMEOUT_MS ?? '20000');

let smokeResolved = false;

function finishSmoke(code, payload) {
  if (!smokeMode || smokeResolved) return;
  smokeResolved = true;
  if (payload) {
    console.log(JSON.stringify(payload));
  }
  app.exit(code);
}

function candidatePythonBins() {
  return [
    process.env.LANDER_PYTHON,
    path.join(repoRoot, '.venv', 'bin', 'python'),
    path.join(repoRoot, '.venv', 'Scripts', 'python.exe'),
    'python3',
    'python',
  ].filter(Boolean);
}

function runWithBinary(binary, args, input) {
  return new Promise((resolve, reject) => {
    const child = spawn(binary, args, {
      cwd: repoRoot,
      env: { ...process.env, PYTHONPATH: path.join(repoRoot, 'src') },
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => {
      stdout += String(chunk);
    });
    child.stderr.on('data', (chunk) => {
      stderr += String(chunk);
    });
    child.on('error', reject);
    child.on('exit', (code) => {
      if (code === 0) {
        resolve(stdout);
      } else {
        reject(new Error(stderr || stdout || `Python bridge exited with code ${code}`));
      }
    });

    if (input) {
      child.stdin.write(input);
    }
    child.stdin.end();
  });
}

async function invokeBridge(commandArgs, payload) {
  let lastError = null;
  for (const binary of candidatePythonBins()) {
    try {
      const output = await runWithBinary(binary, ['-m', 'lander_sim.bridge', ...commandArgs], payload ? JSON.stringify(payload) : undefined);
      return JSON.parse(output);
    } catch (error) {
      lastError = error;
      if (!/ENOENT|not found|No such file/i.test(String(error))) {
        break;
      }
    }
  }
  throw lastError ?? new Error('No usable Python interpreter found for lander bridge');
}

async function collectDiagnostics() {
  try {
    const presetResult = await invokeBridge(['list-presets']);
    return {
      ok: true,
      repoRoot,
      pythonCandidates: candidatePythonBins(),
      presetCount: presetResult?.presets?.length ?? 0,
    };
  } catch (error) {
    return {
      ok: false,
      repoRoot,
      pythonCandidates: candidatePythonBins(),
      error: String(error?.message ?? error),
    };
  }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1700,
    height: 1040,
    show: !smokeMode,
    backgroundColor: '#060b12',
    title: 'Kimchi Lander Sim 2D — Electron',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const devUrl = process.env.ELECTRON_RENDERER_URL;
  if (devUrl) {
    win.loadURL(devUrl);
  } else {
    win.loadFile(path.join(repoRoot, 'electron-app', 'dist', 'index.html'));
  }

  if (smokeMode) {
    win.webContents.on('did-finish-load', async () => {
      try {
        const preloadAvailable = await win.webContents.executeJavaScript('typeof window.landerBridge !== "undefined"');
        const diagnostic = await collectDiagnostics();
        if (!preloadAvailable) {
          finishSmoke(1, {
            ok: false,
            stage: 'preload-missing',
            error: 'window.landerBridge was not available in the packaged renderer',
          });
          return;
        }
        if (!diagnostic.ok) {
          finishSmoke(1, {
            ok: false,
            stage: 'bridge-probe-failed',
            error: diagnostic.error,
            pythonCandidates: diagnostic.pythonCandidates,
          });
          return;
        }
        finishSmoke(0, {
          ok: true,
          stage: 'did-finish-load',
          preloadAvailable,
          presetCount: diagnostic.presetCount,
        });
      } catch (error) {
        finishSmoke(1, {
          ok: false,
          stage: 'smoke-execute-javascript',
          error: String(error?.message ?? error),
        });
      }
    });
    win.webContents.on('did-fail-load', (_event, errorCode, errorDescription, validatedURL) => {
      finishSmoke(1, {
        ok: false,
        stage: 'did-fail-load',
        errorCode,
        errorDescription,
        validatedURL,
      });
    });
    win.webContents.on('render-process-gone', (_event, details) => {
      finishSmoke(1, {
        ok: false,
        stage: 'render-process-gone',
        details,
      });
    });
    setTimeout(() => {
      finishSmoke(1, {
        ok: false,
        stage: 'timeout',
        timeoutMs: smokeTimeoutMs,
      });
    }, smokeTimeoutMs);
  }
}

ipcMain.handle('lander:list-presets', async () => invokeBridge(['list-presets']));
ipcMain.handle('lander:get-preset', async (_event, identifier) => invokeBridge(['get-preset', identifier]));
ipcMain.handle('lander:run-simulation', async (_event, payload) => invokeBridge(['run'], payload));
ipcMain.handle('lander:diagnostics', async () => collectDiagnostics());
ipcMain.on('lander:startup-status', (_event, payload) => {
  if (!smokeMode) return;
  if (payload?.ok) {
    finishSmoke(0, { ok: true, stage: payload.stage ?? 'ready' });
  } else {
    finishSmoke(1, { ok: false, stage: payload?.stage ?? 'startup-error', error: payload?.error ?? 'Unknown startup failure' });
  }
});
ipcMain.handle('lander:save-config', async (_event, payload) => {
  const result = await dialog.showSaveDialog({
    title: 'Save lander configuration',
    defaultPath: path.join(repoRoot, 'lander-config.json'),
    filters: [{ name: 'JSON', extensions: ['json'] }],
  });
  if (result.canceled || !result.filePath) {
    return { canceled: true };
  }
  await fs.writeFile(result.filePath, JSON.stringify(payload, null, 2));
  return { canceled: false, filePath: result.filePath };
});
ipcMain.handle('lander:load-config', async () => {
  const result = await dialog.showOpenDialog({
    title: 'Load lander configuration',
    defaultPath: repoRoot,
    filters: [{ name: 'JSON', extensions: ['json'] }],
    properties: ['openFile'],
  });
  if (result.canceled || !result.filePaths[0]) {
    return { canceled: true };
  }
  const payload = JSON.parse(await fs.readFile(result.filePaths[0], 'utf8'));
  return { canceled: false, filePath: result.filePaths[0], payload };
});

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
