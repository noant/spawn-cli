import pytest

from spawn_cli.cli import main


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])

    assert exc.value.code == 0
    assert "spawn" in capsys.readouterr().out
