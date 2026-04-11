import { spawn } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const repoRoot = path.resolve(path.dirname(__filename), '..');

const child = spawn(process.execPath, [path.join(repoRoot, 'scripts', 'start-app.mjs')], {
  cwd: repoRoot,
  env: {
    ...process.env,
    LANDER_ELECTRON_SMOKE: '1',
    LANDER_ELECTRON_SMOKE_TIMEOUT_MS: process.env.LANDER_ELECTRON_SMOKE_TIMEOUT_MS ?? '20000',
    npm_execpath: process.env.npm_execpath ?? '',
  },
  stdio: ['ignore', 'pipe', 'pipe'],
});

let stdout = '';
let stderr = '';
child.stdout.on('data', (chunk) => {
  stdout += String(chunk);
  process.stdout.write(String(chunk));
});
child.stderr.on('data', (chunk) => {
  stderr += String(chunk);
  process.stderr.write(String(chunk));
});

child.on('error', (error) => {
  console.error(error);
  process.exit(1);
});

child.on('exit', (code) => {
  if (code === 0) {
    process.exit(0);
  }
  if (!stdout && stderr) {
    console.error(stderr);
  }
  process.exit(code ?? 1);
});
