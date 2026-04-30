from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import warnings
from dataclasses import dataclass
from pathlib import Path

from spawn_cli.core.errors import SpawnError, SpawnWarning
from spawn_cli.io.yaml_io import load_yaml
from spawn_cli.models.config import ExtensionConfig
from spawn_cli.models.config import SourceYaml as SY

SCRIPT_ENV_VARS = (
    "SPAWN_EXT_NAME",
    "SPAWN_EXT_PATH",
    "SPAWN_EXT_VERSION",
    "SPAWN_TARGET_VERSION",
    "SPAWN_TARGET_ROOT",
)


def _extend_dir(target_root: Path, extension: str) -> Path:
    return target_root / "spawn" / ".extend" / extension


def _ext_layout_root(target_root: Path, extension: str, override: Path | None) -> Path:
    if override is not None:
        return override
    return _extend_dir(target_root, extension)


def _core_version(target_root: Path) -> str:
    raw = load_yaml(target_root / "spawn" / ".core" / "config.yaml")
    if not raw or not raw.get("version"):
        return "0.0.0"
    return str(raw["version"])


def _setup_script_path(ext_layout: Path, setup_filename: str) -> Path:
    return ext_layout / "setup" / setup_filename


def _extension_config_at(ext_layout: Path) -> ExtensionConfig:
    raw = load_yaml(ext_layout / "config.yaml")
    if not raw:
        raise SpawnError("missing extension config.yaml for script run")
    return ExtensionConfig.model_validate(raw)


def _installed_source_version(target_root: Path, extension: str) -> str | None:
    p = _extend_dir(target_root, extension) / "source.yaml"
    if not p.is_file():
        return None
    raw = load_yaml(p)
    if not raw:
        return None
    sy = SY.model_validate(raw)
    return sy.installed.version


def _run_script(
    target_root: Path,
    extension: str,
    script_filename: str,
    *,
    ext_layout: Path,
    blocking: bool,
) -> subprocess.CompletedProcess[str]:
    script_path = _setup_script_path(ext_layout, script_filename)
    if not script_path.is_file():
        raise SpawnError(f"setup script missing: {script_path}")
    cfg = _extension_config_at(ext_layout)
    ext_ver = cfg.version
    tgt_ver = _core_version(target_root)
    src_ver = _installed_source_version(target_root, extension) or ext_ver
    env = os.environ.copy()
    env["SPAWN_TARGET_ROOT"] = str(target_root.resolve())
    env["SPAWN_EXT_NAME"] = extension
    env["SPAWN_EXT_PATH"] = str(ext_layout.resolve())
    env["SPAWN_EXT_VERSION"] = ext_ver
    env["SPAWN_TARGET_VERSION"] = tgt_ver
    proc = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(target_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        msg = f"script {script_filename!r} failed (exit {proc.returncode})"
        if proc.stderr.strip():
            msg = f"{msg}: {proc.stderr.strip()}"
        if blocking:
            raise SpawnError(msg)
        warnings.warn(msg, SpawnWarning)
    return proc


def run_before_install_scripts(target_root: Path, extension: str, *, ext_layout: Path | None = None) -> None:
    layout = _ext_layout_root(target_root, extension, ext_layout)
    cfg = _extension_config_at(layout)
    if not cfg.setup or not cfg.setup.before_install:
        return
    _run_script(
        target_root,
        extension,
        cfg.setup.before_install,
        ext_layout=layout,
        blocking=True,
    )


def run_after_install_scripts(target_root: Path, extension: str, *, ext_layout: Path | None = None) -> None:
    layout = _ext_layout_root(target_root, extension, ext_layout)
    cfg = _extension_config_at(layout)
    if not cfg.setup or not cfg.setup.after_install:
        return
    _run_script(
        target_root,
        extension,
        cfg.setup.after_install,
        ext_layout=layout,
        blocking=False,
    )


def run_before_uninstall_scripts(target_root: Path, extension: str, *, ext_layout: Path | None = None) -> None:
    layout = _ext_layout_root(target_root, extension, ext_layout)
    cfg = _extension_config_at(layout)
    if not cfg.setup:
        return
    if not cfg.setup.before_uninstall:
        return
    _run_script(
        target_root,
        extension,
        cfg.setup.before_uninstall,
        ext_layout=layout,
        blocking=True,
    )


def run_after_uninstall_scripts(target_root: Path, extension: str, *, ext_layout: Path | None = None) -> None:
    layout = _ext_layout_root(target_root, extension, ext_layout)
    if not layout.is_dir():
        return
    cfg = _extension_config_at(layout)
    if not cfg.setup or not cfg.setup.after_uninstall:
        return
    _run_script(
        target_root,
        extension,
        cfg.setup.after_uninstall,
        ext_layout=layout,
        blocking=False,
    )


@dataclass
class AfterUninstallSnapshot:
    script_path: Path | None
    ext_version: str


def snapshot_after_uninstall_script(ext_dir: Path, cfg: ExtensionConfig) -> AfterUninstallSnapshot:
    if not cfg.setup or not cfg.setup.after_uninstall:
        return AfterUninstallSnapshot(None, cfg.version)
    src = ext_dir / "setup" / cfg.setup.after_uninstall
    if not src.is_file():
        return AfterUninstallSnapshot(None, cfg.version)
    td = Path(tempfile.mkdtemp(prefix="spawn-after-uninstall-"))
    dst = td / src.name
    shutil.copy2(src, dst)
    return AfterUninstallSnapshot(dst, cfg.version)


def run_after_uninstall_from_snapshot(
    target_root: Path, extension: str, snap: AfterUninstallSnapshot
) -> None:
    if snap.script_path is None:
        return
    ghost_ext = _extend_dir(target_root, extension)
    env = os.environ.copy()
    env["SPAWN_TARGET_ROOT"] = str(target_root.resolve())
    env["SPAWN_EXT_NAME"] = extension
    env["SPAWN_EXT_PATH"] = str(ghost_ext.resolve())
    env["SPAWN_EXT_VERSION"] = snap.ext_version
    env["SPAWN_TARGET_VERSION"] = _core_version(target_root)
    proc = subprocess.run(
        [sys.executable, str(snap.script_path)],
        cwd=str(target_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        msg = f"after-uninstall script failed (exit {proc.returncode})"
        if proc.stderr.strip():
            msg = f"{msg}: {proc.stderr.strip()}"
        warnings.warn(msg, SpawnWarning)


def run_healthcheck_scripts(target_root: Path, extension: str, *, ext_layout: Path | None = None) -> bool:
    layout = _ext_layout_root(target_root, extension, ext_layout)
    cfg = _extension_config_at(layout)
    if not cfg.setup or not cfg.setup.healthcheck:
        return True
    proc = subprocess.run(
        [
            sys.executable,
            str(_setup_script_path(layout, cfg.setup.healthcheck)),
        ],
        cwd=str(target_root),
        env={
            **os.environ,
            "SPAWN_TARGET_ROOT": str(target_root.resolve()),
            "SPAWN_EXT_NAME": extension,
            "SPAWN_EXT_PATH": str(layout.resolve()),
            "SPAWN_EXT_VERSION": cfg.version,
            "SPAWN_TARGET_VERSION": _core_version(target_root),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


__all__ = [
    "AfterUninstallSnapshot",
    "SCRIPT_ENV_VARS",
    "_run_script",
    "run_after_install_scripts",
    "run_after_uninstall_scripts",
    "run_before_install_scripts",
    "run_before_uninstall_scripts",
    "run_after_uninstall_from_snapshot",
    "run_healthcheck_scripts",
    "snapshot_after_uninstall_script",
]
