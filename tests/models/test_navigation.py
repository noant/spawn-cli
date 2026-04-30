from __future__ import annotations

import pytest
from pydantic import ValidationError

from spawn_cli.models.navigation import NavExtGroup, NavFile, NavRulesGroup, NavigationFile


def test_nav_file() -> None:
    f = NavFile.model_validate({"path": "spawn/x.md", "description": "d"})
    assert f.path == "spawn/x.md"
    assert f.description == "d"


def test_nav_ext_group_defaults() -> None:
    g = NavExtGroup.model_validate({"ext": "e"})
    assert g.ext == "e"
    assert g.files == []


def test_nav_rules_group() -> None:
    g = NavRulesGroup.model_validate({"rules": [{"path": "spawn/rules/a.yaml", "description": "r"}]})
    assert len(g.rules) == 1
    assert g.rules[0].path == "spawn/rules/a.yaml"


def test_navigation_file_aliases() -> None:
    n = NavigationFile.model_validate(
        {
            "read-required": [{"ext": "x", "files": [{"path": "a.md", "description": ""}]}],
            "read-contextual": [],
        }
    )
    assert len(n.read_required) == 1
    assert n.read_contextual == []


def test_navigation_file_invalid_shape() -> None:
    with pytest.raises(ValidationError):
        NavigationFile.model_validate({"read-required": "nope"})  # type: ignore[arg-type]
