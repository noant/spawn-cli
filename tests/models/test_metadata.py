from __future__ import annotations

import pytest
from pydantic import ValidationError

from spawn_cli.models.metadata import RenderedMcpEntry, RenderedMcpMeta, RenderedSkillEntry, RenderedSkillsMeta


def test_rendered_skill_entry() -> None:
    e = RenderedSkillEntry.model_validate({"skill": "s.md", "path": ".cursor/skills/s/SKILL.md"})
    assert e.skill == "s.md"
    assert e.path == ".cursor/skills/s/SKILL.md"


def test_rendered_skills_meta_default_extensions() -> None:
    m = RenderedSkillsMeta.model_validate({})
    assert m.extensions == {}


def test_rendered_skills_meta_populated() -> None:
    m = RenderedSkillsMeta.model_validate(
        {
            "extensions": {
                "ext": [{"skill": "a.md", "path": "p1"}],
            }
        }
    )
    assert len(m.extensions["ext"]) == 1
    assert m.extensions["ext"][0].skill == "a.md"


def test_rendered_mcp_entry_requires_name() -> None:
    RenderedMcpEntry.model_validate({"name": "srv"})
    with pytest.raises(ValidationError):
        RenderedMcpEntry.model_validate({})


def test_rendered_mcp_meta() -> None:
    m = RenderedMcpMeta.model_validate({"extensions": {"x": [{"name": "a"}, {"name": "b"}]}})
    assert [e.name for e in m.extensions["x"]] == ["a", "b"]
