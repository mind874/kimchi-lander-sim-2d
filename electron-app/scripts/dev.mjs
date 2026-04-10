import { spawn } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const rendererUrl = 'http://127.0.0.1:4173';
const __filename = fileURLToPath(import.meta.url);
const appDir = path.resolve(path.dirname(__filename), '..');

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForServer(url, timeoutMs = 30000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // keep polling
    }
    await wait(400);
  }
  throw new Error(`Timed out waiting for ${url}`);
}

const devServer = spawn(process.platform === 'win32' ? 'npx.cmd' : 'npx', ['vite', '--host', '127.0.0.1', '--port', '4173'], {
  cwd: appDir,
  stdio: 'inherit',
});

await waitForServer(rendererUrl);

const electron = spawn(process.platform === 'win32' ? 'npx.cmd' : 'npx', ['electron', '.'], {
  cwd: appDir,
  stdio: 'inherit',
  env: { ...process.env, ELECTRON_RENDERER_URL: rendererUrl },
});

const shutdown = () => {
  devServer.kill('SIGTERM');
  electron.kill('SIGTERM');
};

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

electron.on('exit', (electronCode) => {
  devServer.kill('SIGTERM');
  process.exit(electronCode ?? 0);
});
