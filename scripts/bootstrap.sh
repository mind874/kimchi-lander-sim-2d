#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "error: python3 is required" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "error: npm is required" >&2
  exit 1
fi

if [ ! -d .venv ]; then
  "$PYTHON_BIN" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . pytest
npm --prefix electron-app install

cat <<'MSG'
Bootstrap complete.

Primary GUI (Electron + React):
  npm run electron:dev

Verification:
  npm run python:test
  npm run bridge:list-presets
  npm run electron:build

Python no longer ships a standalone PySide GUI. Use:
  python -m lander_sim
for launch guidance, or:
  python -m lander_sim bridge list-presets
for bridge CLI access.
MSG
