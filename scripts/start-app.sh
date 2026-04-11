#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="launch"
if [[ "${1:-}" == "--setup-only" ]]; then
  MODE="setup-only"
elif [[ "${1:-}" == "--dev" ]]; then
  MODE="dev"
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

if [[ "$MODE" == "dev" ]]; then
  echo "Starting Kimchi Lander Sim 2D in dev mode..."
  exec npm run electron:dev
fi

echo "Building and starting Kimchi Lander Sim 2D..."
npm run electron:build
exec npm run electron:start
