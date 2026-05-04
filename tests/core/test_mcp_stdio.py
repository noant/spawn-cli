from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from spawn_cli.core import low_level as ll
from spawn_cli.core.errors import SpawnError
from spawn_cli.core import mcp_stdio


def _stub_proxy_extension(tmp_path: Path, *, cwd: str = ".", env_lit: dict | None = None) -> None:
    ll.init(tmp_path)
    root = tmp_path / "spawn" / ".extend" / "spectask"
    root.mkdir(parents=True)
    env = env_lit or {}
    mcp = {
        "servers": [
            {
                "name": "proxied",
                "spawn_stdio_proxy": True,
                "transport": {
                    "type": "stdio",
                    "command": "noop-cmd",
                    "args": ["a", "b"],
                    "cwd": cwd,
                },
                "env": env,
            },
        ]
    }
    mdir = root / "mcp"
    mdir.mkdir(parents=True)
    body = json.dumps(mcp)
    for plat in ("windows", "linux", "macos"):
        (mdir / f"{plat}.json").write_text(body, encoding="utf-8")


def test_run_mcp_stdio_proxy_unknown_extension(tmp_path: Path) -> None:
    ll.init(tmp_path)
    with pytest.raises(SpawnError, match="unknown extension"):
        mcp_stdio.run_mcp_stdio_proxy(tmp_path, "missing", "x")


def test_run_mcp_stdio_proxy_unknown_server(tmp_path: Path) -> None:
    _stub_proxy_extension(tmp_path)
    with pytest.raises(SpawnError, match="unknown MCP server"):
        mcp_stdio.run_mcp_stdio_proxy(tmp_path, "spectask", "nonesuch")


def test_run_mcp_stdio_proxy_rejects_non_stdio_transport(tmp_path: Path) -> None:
    ll.init(tmp_path)
    root = tmp_path / "spawn" / ".extend" / "spectask"
    root.mkdir(parents=True)
    mcp = {
        "servers": [
            {
                "name": "bad-transport",
                "spawn_stdio_proxy": True,
                "transport": {
                    "type": "sse",
                    "url": "https://example.com/mcp",
                },
                "env": {},
            },
        ]
    }
    mdir = root / "mcp"
    mdir.mkdir(parents=True)
    body = json.dumps(mcp)
    for plat in ("windows", "linux", "macos"):
        (mdir / f"{plat}.json").write_text(body, encoding="utf-8")

    with pytest.raises(SpawnError, match='spawn mcp_stdio requires type "stdio"'):
        mcp_stdio.run_mcp_stdio_proxy(tmp_path, "spectask", "bad-transport")


def test_run_mcp_stdio_proxy_rejects_without_flag(tmp_path: Path) -> None:
    ll.init(tmp_path)
    root = tmp_path / "spawn" / ".extend" / "spectask"
    root.mkdir(parents=True)
    mcp = {
        "servers": [
            {
                "name": "inline",
                "spawn_stdio_proxy": False,
                "transport": {"type": "stdio", "command": "c", "args": [], "cwd": "."},
                "env": {},
            },
        ]
    }
    mdir = root / "mcp"
    mdir.mkdir(parents=True)
    body = json.dumps(mcp)
    for plat in ("windows", "linux", "macos"):
        (mdir / f"{plat}.json").write_text(body, encoding="utf-8")

    with pytest.raises(SpawnError, match="spawn_stdio_proxy"):
        mcp_stdio.run_mcp_stdio_proxy(tmp_path, "spectask", "inline")


def test_run_mcp_stdio_proxy_popen_inherit_stdio(tmp_path: Path) -> None:
    _stub_proxy_extension(
        tmp_path,
        cwd="subdir",
        env_lit={"K": {"source": "user", "required": False, "secret": False, "value": "v"}},
    )
    (tmp_path / "subdir").mkdir()
    root = tmp_path.resolve()

    mock_proc = MagicMock()
    mock_proc.wait.return_value = 42
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_proc
    mock_cm.__exit__.return_value = None

    with patch("spawn_cli.core.mcp_stdio.subprocess.Popen", return_value=mock_cm) as popen:
        code = mcp_stdio.run_mcp_stdio_proxy(root, "spectask", "proxied")

    assert code == 42
    kwargs = popen.call_args.kwargs
    assert kwargs["cwd"] == str((root / "subdir").resolve())
    assert kwargs["env"]["K"] == "v"
    assert kwargs["stdin"] is sys.stdin.buffer
    assert kwargs["stdout"] is sys.stdout.buffer
    assert kwargs["stderr"] is None
    assert kwargs["shell"] is False
    assert kwargs["bufsize"] == 0
    assert popen.call_args.args[0] == ["noop-cmd", "a", "b"]
