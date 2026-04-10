from __future__ import annotations

from lander_sim import __main__ as cli



def test_cli_main_prints_react_frontend_guidance(capsys) -> None:
    exit_code = cli.main([])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert 'Electron + React frontend' in captured.out
    assert 'python -m lander_sim bridge list-presets' in captured.out



def test_cli_bridge_subcommand_delegates(capsys) -> None:
    exit_code = cli.main(['bridge', 'list-presets'])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert 'presets' in captured.out
