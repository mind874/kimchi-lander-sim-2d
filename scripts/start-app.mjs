import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const rootDir = path.resolve(path.dirname(__filename), '..');
const mode = process.argv[2] ?? 'launch';

function npmInvocation(args) {
  if (process.env.npm_execpath) {
    return {
      command: process.execPath,
      args: [process.env.npm_execpath, ...args],
    };
  }
  if (process.platform === 'win32') {
    return {
      command: 'npm.cmd',
      args,
    };
  }
  return {
    command: '/usr/bin/env',
    args: ['npm', ...args],
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
  const needsBootstrap = !fs.existsSync(path.join(rootDir, '.venv')) || !fs.existsSync(path.join(rootDir, 'electron-app', 'node_modules'));
  if (!needsBootstrap) {
    console.log('Using existing app environment.');
    return;
  }
  console.log('Preparing the app environment...');
  await spawnLogged(path.join(rootDir, 'scripts', 'bootstrap.sh'), []);
}

async function buildRenderer() {
  console.log('Building Electron renderer...');
  const npm = npmInvocation(['--prefix', 'electron-app', 'run', 'build']);
  await spawnLogged(npm.command, npm.args);
}

async function launchElectron(extraEnv = {}) {
  console.log('Starting Kimchi Lander Sim 2D...');
  const npm = npmInvocation(['--prefix', 'electron-app', 'run', 'start']);
  await spawnLogged(npm.command, npm.args, { env: extraEnv });
}

async function main() {
  await ensureEnvironment();

  if (mode === 'setup-only') {
    console.log('Setup complete. Launch with: npm start');
    return;
  }

  if (mode === 'dev') {
    console.log('Starting Kimchi Lander Sim 2D in dev mode...');
    const npm = npmInvocation(['--prefix', 'electron-app', 'run', 'dev']);
    await spawnLogged(npm.command, npm.args);
    return;
  }

  await buildRenderer();
  await launchElectron();
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
