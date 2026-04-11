#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="launch"
if [[ "${1:-}" == "--setup-only" ]]; then
  MODE="setup-only"
fi

if [[ ! -d .venv || ! -d electron-app/node_modules ]]; then
  echo "Preparing the app environment..."
  ./scripts/bootstrap.sh
else
  echo "Using existing app environment."
fi

if [[ "$MODE" == "setup-only" ]]; then
  echo "Setup complete. Launch with: npm start"
  exit 0
fi

echo "Starting Kimchi Lander Sim 2D..."
exec npm run electron:dev
