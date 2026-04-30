from __future__ import annotations

import pytest
from pydantic import ValidationError

from spawn_cli.models.skill import SkillFileRef, SkillMetadata, SkillRawInfo


def test_skill_file_ref() -> None:
    r = SkillFileRef.model_validate({"file": "f.md", "description": "d"})
    assert r.file == "f.md"
    assert r.description == "d"


def test_skill_raw_info_required_read_alias() -> None:
    i = SkillRawInfo.model_validate(
        {"name": "n", "description": "d", "content": "body", "required-read": ["a.md"]}
    )
    assert i.required_read == ["a.md"]
    assert i.content == "body"


def test_skill_raw_info_default_required_read() -> None:
    i = SkillRawInfo.model_validate({"name": "n", "description": "d", "content": ""})
    assert i.required_read == []


def test_skill_metadata_lists_default() -> None:
    m = SkillMetadata.model_validate(
        {"name": "n", "description": "d", "content": "c"},
    )
    assert m.required_read == []
    assert m.auto_read == []


def test_skill_metadata_invalid() -> None:
    with pytest.raises(ValidationError):
        SkillMetadata.model_validate({"name": "n"})  # missing fields
