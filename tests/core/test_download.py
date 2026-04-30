from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from ruamel.yaml import YAML

from spawn_cli.core import download as dl
from spawn_cli.core import high_level as hl
from spawn_cli.core import low_level as ll
from spawn_cli.core.errors import SpawnError

YAML_S = YAML(typ="safe")


def _write_yaml(p: Path, data: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        YAML_S.dump(data, fh)


def _ext_layout(tmp: Path, name: str, version: str = "1.0.0", **extra) -> Path:
    extsrc = tmp / "extsrc"
    extsrc.mkdir(parents=True)
    base = {
        "name": name,
        "version": version,
        "schema": 1,
        "files": {},
        "folders": {},
        "agent-ignore": [],
        "git-ignore": [],
        "skills": {},
        "setup": {},
    }
    base.update(extra)
    _write_yaml(extsrc / "config.yaml", base)
    return tmp


def test_download_local_path(tmp_path: Path) -> None:
    ll.init(tmp_path)
    src = _ext_layout(tmp_path / "src", "localx", files={"hello.txt": {"mode": "static", "globalRead": "no", "localRead": "no"}})
    (src / "extsrc" / "files").mkdir(exist_ok=True)
    (src / "extsrc" / "files" / "hello.txt").write_text("hi", encoding="utf-8")
    with patch("spawn_cli.core.high_level._refresh_extension_core"), patch(
        "spawn_cli.core.high_level.scripts.run_after_install_scripts"
    ):
        dl.install_extension(tmp_path, str(src / "extsrc"))
    dest = tmp_path / "spawn" / ".extend" / "localx"
    assert (dest / "config.yaml").is_file()
    assert (tmp_path / "hello.txt").read_text(encoding="utf-8") == "hi"


def test_download_conflict_error(tmp_path: Path) -> None:
    ll.init(tmp_path)
    a_root = _ext_layout(
        tmp_path / "sra",
        "a",
        files={"conflict.md": {"mode": "static", "globalRead": "no", "localRead": "no"}},
    )
    (a_root / "extsrc" / "files").mkdir(exist_ok=True)
    (a_root / "extsrc" / "files" / "conflict.md").write_text("x", encoding="utf-8")
    with patch("spawn_cli.core.high_level._refresh_extension_core"), patch(
        "spawn_cli.core.high_level.scripts.run_after_install_scripts"
    ):
        dl.install_extension(tmp_path, str(a_root / "extsrc"))
    b_root = _ext_layout(
        tmp_path / "srb",
        "b",
        files={"conflict.md": {"mode": "static", "globalRead": "no", "localRead": "no"}},
    )
    (b_root / "extsrc" / "files").mkdir(exist_ok=True)
    (b_root / "extsrc" / "files" / "conflict.md").write_text("y", encoding="utf-8")
    with pytest.raises(SpawnError, match="File conflict"):
        dl.download_extension(tmp_path, str(b_root / "extsrc"))


def test_download_version_check(tmp_path: Path) -> None:
    ll.init(tmp_path)
    s1 = _ext_layout(tmp_path / "s1", "verext", version="1.0.0")
    with patch("spawn_cli.core.high_level._refresh_extension_core"), patch(
        "spawn_cli.core.high_level.scripts.run_after_install_scripts"
    ):
        dl.install_extension(tmp_path, str(s1 / "extsrc"))
    with pytest.raises(SpawnError, match="newer"):
        dl.download_extension(tmp_path, str(s1 / "extsrc"))


def test_install_build(tmp_path: Path) -> None:
    ll.init(tmp_path)
    build = tmp_path / "build"
    e1_root = _ext_layout(build / "e1", "pack-one")
    e2_root = _ext_layout(build / "e2", "pack-two")
    _write_yaml(
        build / "extensions.yaml",
        {"extensions": [{"path": str(e1_root / "extsrc")}, {"path": str(e2_root / "extsrc")}]},
    )
    with patch("spawn_cli.core.high_level._refresh_extension_core"), patch(
        "spawn_cli.core.high_level.scripts.run_after_install_scripts"
    ):
        dl.install_build(tmp_path, str(build))
    assert sorted(ll.list_extensions(tmp_path)) == ["pack-one", "pack-two"]
