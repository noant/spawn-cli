from __future__ import annotations

import warnings
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

import pytest

from spawn_cli.core import scripts
from spawn_cli.core.errors import SpawnError, SpawnWarning
from spawn_cli.core import low_level as ll
from spawn_cli.io.yaml_io import save_yaml


def _write_ext(
    tmp: Path,
    ext_id: str,
    *,
    setup: dict | None = None,
    script_rel: str | None = None,
    script_body: str = "raise SystemExit(0)\n",
) -> Path:
    ll.init(tmp)
    root = tmp / "spawn" / ".extend" / ext_id
    (root / "setup").mkdir(parents=True, exist_ok=True)
    cfg: dict = {"name": ext_id, "version": "1.0.0", "schema": 1}
    if setup is not None:
        cfg["setup"] = setup
    save_yaml(root / "config.yaml", cfg)
    if script_rel is not None:
        (root / "setup" / script_rel).write_text(script_body, encoding="utf-8")
    return root


def test_run_before_install_success(tmp_path: Path) -> None:
    _write_ext(
        tmp_path,
        "e",
        setup={"before-install": "hook.py"},
        script_rel="hook.py",
    )
    scripts.run_before_install_scripts(tmp_path, "e")


def test_run_before_install_failure(tmp_path: Path) -> None:
    _write_ext(
        tmp_path,
        "e",
        setup={"before-install": "hook.py"},
        script_rel="hook.py",
        script_body="raise SystemExit(2)\n",
    )
    with pytest.raises(SpawnError, match="hook.py"):
        scripts.run_before_install_scripts(tmp_path, "e")


def test_run_after_install_failure_warns(tmp_path: Path) -> None:
    _write_ext(
        tmp_path,
        "e",
        setup={"after-install": "hook.py"},
        script_rel="hook.py",
        script_body="raise SystemExit(1)\n",
    )
    with warnings.catch_warnings(record=True) as wrec:
        warnings.simplefilter("always")
        scripts.run_after_install_scripts(tmp_path, "e")
    assert any(issubclass(w.category, SpawnWarning) for w in wrec)


def test_run_before_uninstall_failure_blocks(tmp_path: Path) -> None:
    _write_ext(
        tmp_path,
        "e",
        setup={"before-uninstall": "hook.py"},
        script_rel="hook.py",
        script_body="raise SystemExit(7)\n",
    )
    with pytest.raises(SpawnError, match="hook.py"):
        scripts.run_before_uninstall_scripts(tmp_path, "e")


def test_run_before_uninstall_skipped_when_absent(tmp_path: Path) -> None:
    _write_ext(tmp_path, "e")
    with patch("spawn_cli.core.scripts.subprocess.run") as run:
        scripts.run_before_uninstall_scripts(tmp_path, "e")
    run.assert_not_called()


def test_no_script_configured_before_install(tmp_path: Path) -> None:
    _write_ext(tmp_path, "e")
    with patch("spawn_cli.core.scripts.subprocess.run") as run:
        scripts.run_before_install_scripts(tmp_path, "e")
    run.assert_not_called()


def test_env_vars_passed(tmp_path: Path) -> None:
    _write_ext(
        tmp_path,
        "e",
        setup={"before-install": "hook.py"},
        script_rel="hook.py",
    )
    fake = CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch("spawn_cli.core.scripts.subprocess.run", return_value=fake) as run:
        scripts.run_before_install_scripts(tmp_path, "e")
    run.assert_called_once()
    kwargs = run.call_args.kwargs
    assert kwargs["env"]["SPAWN_EXT_NAME"] == "e"
    assert kwargs["env"]["SPAWN_TARGET_ROOT"] == str(tmp_path.resolve())
    assert "SPAWN_EXT_PATH" in kwargs["env"]
    assert kwargs["env"]["SPAWN_EXT_VERSION"] == "1.0.0"


def test_run_before_install_prints_progress_to_stderr(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_ext(
        tmp_path,
        "e",
        setup={"before-install": "hook.py"},
        script_rel="hook.py",
    )
    fake = CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch("spawn_cli.core.scripts.subprocess.run", return_value=fake):
        scripts.run_before_install_scripts(tmp_path, "e")
    err = capsys.readouterr().err
    assert "spawn: running before-install script: hook.py" in err
