from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def target_root(tmp_path) -> Path:
    """A temp directory representing a target repository."""
    return tmp_path


@pytest.fixture
def spawn_root(target_root) -> Path:
    root = target_root / "spawn"
    root.mkdir()
    (root / ".metadata").mkdir()
    (root / ".extend").mkdir()
    (root / "rules").mkdir()
    (root / ".core").mkdir()
    return root


@pytest.fixture
def mock_extension(target_root, spawn_root) -> str:
    """Creates a minimal installed extension 'test-ext' with config, skills, mcp."""
    ext_dir = spawn_root / ".extend" / "test-ext"
    ext_dir.mkdir()
    (ext_dir / "skills").mkdir()
    (ext_dir / "files").mkdir()
    (ext_dir / "setup").mkdir()

    (ext_dir / "config.yaml").write_text(
        """
name: test-ext
version: "1.0.0"
schema: 1
files:
  methodology/guide.md:
    description: Core guide.
    mode: static
    globalRead: required
    localRead: required
agent-ignore:
  - spawn/.extend/**
git-ignore:
  - .spawn-cache/**
skills:
  test-skill.md:
    name: test-skill
    description: A test skill.
""",
        encoding="utf-8",
    )

    (ext_dir / "skills" / "test-skill.md").write_text(
        """---
name: test-skill
description: A test skill.
---
Do the work.
""",
        encoding="utf-8",
    )

    import json

    mdir = ext_dir / "mcp"
    mdir.mkdir(parents=True)
    body = json.dumps(
        {
            "servers": [
                {
                    "name": "test-server",
                    "transport": {"type": "stdio", "command": "uvx", "args": ["test-server-mcp"]},
                },
            ],
        }
    )
    for plat in ("windows", "linux", "macos"):
        (mdir / f"{plat}.json").write_text(body, encoding="utf-8")
    return "test-ext"
