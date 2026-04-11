import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const rootDir = path.resolve(path.dirname(__filename), '..');
const mode = process.argv[2] ?? 'launch';
const electronDir = path.join(rootDir, 'electron-app');

function localNodeModuleScript(modulePath, args = []) {
  return {
    command: process.execPath,
    args: [path.join(electronDir, 'node_modules', ...modulePath.split('/')), ...args],
  };
}

function spawnLogged(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: rootDir,
      stdio: 'inherit',
      env: { ...process.env, ...(options.env ?? {}) },
      ...options,
    });
    child.on('error', reject);
    child.on('exit', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`${command} ${args.join(' ')} exited with code ${code ?? 1}`));
      }
    });
  });
}

async function ensureEnvironment() {
  const needsBootstrap =
    !fs.existsSync(path.join(rootDir, '.venv')) ||
    !fs.existsSync(path.join(electronDir, 'node_modules')) ||
    !fs.existsSync(path.join(electronDir, 'node_modules', 'electron', 'cli.js')) ||
    !fs.existsSync(path.join(electronDir, 'node_modules', 'vite', 'bin', 'vite.js'));
  if (!needsBootstrap) {
    console.log('Using existing app environment.');
    return;
  }
  console.log('Preparing the app environment...');
  await spawnLogged(path.join(rootDir, 'scripts', 'bootstrap.sh'), []);
}

async function buildRenderer() {
  console.log('Building Electron renderer...');
  const vite = localNodeModuleScript('vite/bin/vite.js', ['build']);
  await spawnLogged(vite.command, vite.args, { cwd: electronDir });
}

async function launchElectron(extraEnv = {}) {
  console.log('Starting Kimchi Lander Sim 2D...');
  const electron = localNodeModuleScript('electron/cli.js', ['.']);
  await spawnLogged(electron.command, electron.args, { cwd: electronDir, env: extraEnv });
}

async function main() {
  await ensureEnvironment();

  if (mode === 'setup-only') {
    console.log('Setup complete. Launch with: npm start');
    return;
  }

  if (mode === 'dev') {
    console.log('Starting Kimchi Lander Sim 2D in dev mode...');
    await spawnLogged(process.execPath, [path.join(electronDir, 'scripts', 'dev.mjs')], { cwd: electronDir });
    return;
  }

  await buildRenderer();
  await launchElectron();
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
