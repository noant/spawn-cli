from __future__ import annotations

import contextlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from spawn_cli.cli import main
from spawn_cli.core.errors import SpawnError
from spawn_cli.ide.registry import DetectResult, IdeCapabilities


@contextlib.contextmanager
def _noop_lock(_target_root: Path):
    yield


def test_spawn_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "spawn" in capsys.readouterr().out


def test_spawn_extension_add_help_shows_argument_descriptions(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["extension", "add", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--branch" in out
    assert "Git" in out or "git" in out


def test_spawn_init(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path.resolve()
    mock_init = MagicMock()

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.ll.init", mock_init
    ):
        assert main(["init"]) == 0

    mock_init.assert_called_once_with(root)


def test_spawn_need_init(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["rules", "refresh"]) == 1
    err = capsys.readouterr().err
    assert "need init before" in err


def test_spawn_lock_busy(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()

    count = {"n": 0}

    @contextlib.contextmanager
    def counting_lock(_target_root: Path):
        count["n"] += 1
        if count["n"] == 2:
            raise SpawnError("Операция в процессе (файл lock detected)")
        yield

    with patch("spawn_cli.cli.spawn_lock", counting_lock), patch(
        "spawn_cli.cli.hl.refresh_rules_navigation", MagicMock()
    ):
        assert main(["rules", "refresh"]) == 0
        assert main(["rules", "refresh"]) == 1

    assert "Операция в процессе" in capsys.readouterr().err


def test_spawn_rules_refresh(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()
    root = tmp_path.resolve()
    mock_refresh = MagicMock()

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.hl.refresh_rules_navigation", mock_refresh
    ):
        assert main(["rules", "refresh"]) == 0

    mock_refresh.assert_called_once_with(root)


def test_spawn_refresh(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from spawn_cli.core import low_level as ll

    ll.init(tmp_path)
    root = tmp_path.resolve()
    mock_repo = MagicMock()

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.hl.refresh_repository", mock_repo
    ):
        assert main(["refresh"]) == 0

    mock_repo.assert_called_once_with(root)


def test_spawn_refresh_need_init(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["refresh"]) == 1
    assert "need init before" in capsys.readouterr().err


def test_spawn_ide_list_supported_ides(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()
    root = tmp_path.resolve()
    sample = {
        "cursor": DetectResult(
            True,
            IdeCapabilities("native", "project", "native", "agents-md"),
        )
    }

    mock_detect = MagicMock(return_value=sample)

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.detect_supported_ides", mock_detect
    ):
        assert main(["ide", "list-supported-ides"]) == 0

    mock_detect.assert_called_once_with(root)
    out = capsys.readouterr().out
    assert "cursor" in out
    assert "used-in-repo" in out


def test_spawn_ide_add(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()
    root = tmp_path.resolve()
    mock_add = MagicMock()

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.hl.add_ide", mock_add
    ):
        assert main(["ide", "add", "cursor", "codex"]) == 0

    assert mock_add.call_args_list == [
        ((root, "cursor"),),
        ((root, "codex"),),
    ]


def test_spawn_ide_remove(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()
    root = tmp_path.resolve()
    mock_remove = MagicMock()

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.hl.remove_ide", mock_remove
    ):
        assert main(["ide", "remove", "cursor"]) == 0

    mock_remove.assert_called_once_with(root, "cursor")


def test_spawn_ide_list(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()
    root = tmp_path.resolve()
    mock_list = MagicMock(return_value=["cursor", "codex"])

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.ll.list_ides", mock_list
    ):
        assert main(["ide", "list"]) == 0

    mock_list.assert_called_once_with(root)
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    assert lines == ["cursor", "codex"]


def test_spawn_extension_add(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()
    root = tmp_path.resolve()
    mock_install = MagicMock()

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.dl.install_extension", mock_install
    ):
        assert main(["extension", "add", "https://example.com/ext.git", "--branch", "main"]) == 0

    mock_install.assert_called_once_with(
        root, "https://example.com/ext.git", "main"
    )


def test_spawn_extension_update(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()
    root = tmp_path.resolve()
    mock_up = MagicMock()

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.hl.update_extension", mock_up
    ):
        assert main(["extension", "update", "my-ext"]) == 0

    mock_up.assert_called_once_with(root, "my-ext")


def test_spawn_extension_remove(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()
    root = tmp_path.resolve()
    mock_rm = MagicMock()

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.hl.remove_extension", mock_rm
    ):
        assert main(["extension", "remove", "my-ext"]) == 0

    mock_rm.assert_called_once_with(root, "my-ext")


def test_spawn_extension_reinstall(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()
    root = tmp_path.resolve()
    mock_re = MagicMock()

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.hl.reinstall_extension", mock_re
    ):
        assert main(["extension", "reinstall", "my-ext"]) == 0

    mock_re.assert_called_once_with(root, "my-ext")


def test_spawn_extension_list(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()
    root = tmp_path.resolve()
    mock_list = MagicMock(return_value=["a", "b"])

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.ll.list_extensions", mock_list
    ):
        assert main(["extension", "list"]) == 0

    mock_list.assert_called_once_with(root)
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    assert lines == ["a", "b"]


def test_spawn_extension_init(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()
    sub = tmp_path / "sub"
    sub.mkdir()
    mock_init = MagicMock()

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.hl.extension_init", mock_init
    ):
        assert main(["extension", "init", str(sub), "--name", "x"]) == 0

    mock_init.assert_called_once_with(sub.resolve(), "x")


def test_spawn_extension_check(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()
    chk = tmp_path / "chk"
    chk.mkdir()
    mock_check = MagicMock(return_value=["missing skill"])

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.hl.extension_check", mock_check
    ):
        assert main(["extension", "check", str(chk)]) == 0

    mock_check.assert_called_once_with(chk.resolve(), strict=False)
    assert "Warning: missing skill" in capsys.readouterr().out


def test_spawn_extension_healthcheck_ok(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.hl.extension_healthcheck", return_value=True
    ):
        assert main(["extension", "healthcheck", "ext"]) == 0


def test_spawn_extension_healthcheck_fail(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.hl.extension_healthcheck", return_value=False
    ):
        assert main(["extension", "healthcheck", "ext"]) == 1


def test_spawn_build_install(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()
    root = tmp_path.resolve()
    mock_install = MagicMock()

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.dl.install_build", mock_install
    ):
        assert main(["build", "install", "./manifest.yaml"]) == 0

    mock_install.assert_called_once_with(root, "./manifest.yaml", None)


def test_spawn_build_list(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()
    mock_list = MagicMock(return_value=[{"url": "u"}])

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.dl.list_build_extensions", mock_list
    ):
        assert main(["build", "list", "./manifest.yaml"]) == 0

    mock_list.assert_called_once_with("./manifest.yaml", None)
    assert "url" in capsys.readouterr().out


def test_spawn_error_exit_code(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spawn").mkdir()

    def boom(*_a, **_kw):
        raise SpawnError("planned failure")

    with patch("spawn_cli.cli.spawn_lock", _noop_lock), patch(
        "spawn_cli.cli.hl.refresh_rules_navigation", boom
    ):
        assert main(["rules", "refresh"]) == 1

    assert "planned failure" in capsys.readouterr().err
