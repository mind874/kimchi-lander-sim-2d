from __future__ import annotations

import sys

from lander_sim.bridge import main as bridge_main


HELP_TEXT = """Kimchi Lander Sim 2D now uses the Electron + React frontend as the primary GUI.

Recommended launch:
  ./scripts/bootstrap.sh
  npm run electron:dev

Bridge CLI examples:
  python -m lander_sim bridge list-presets
  python -m lander_sim bridge get-preset stable_hover.json
  python -m lander_sim bridge run --config-file path/to/config.json
"""


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == 'bridge':
        return bridge_main(args[1:])
    print(HELP_TEXT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
