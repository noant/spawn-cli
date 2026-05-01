from __future__ import annotations

import pytest
from pydantic import ValidationError

from spawn_cli.models.config import (
    CoreConfig,
    ExtensionConfig,
    ExtensionFileEntry,
    ExtensionFolderEntry,
    ExtensionHints,
    FileMode,
    IdeList,
    ReadFlag,
    SkillEntry,
    SourceYaml,
    SetupConfig,
)


def test_extension_file_entry_defaults_and_aliases() -> None:
    e = ExtensionFileEntry.model_validate(
        {"globalRead": "required", "localRead": "no", "mode": "static"}
    )
    assert e.globalRead is ReadFlag.required
    assert e.localRead is ReadFlag.no
    assert e.mode is FileMode.static
    assert e.description is None


def test_extension_file_entry_invalid_global_read() -> None:
    with pytest.raises(ValidationError):
        ExtensionFileEntry(globalRead="maybe")  # type: ignore[arg-type]


def test_skill_entry_required_read_alias() -> None:
    s = SkillEntry.model_validate({"required-read": ["a.md", "b.md"]})
    assert s.required_read == ["a.md", "b.md"]
    assert s.name is None
    assert s.description is None


def test_setup_config_script_aliases() -> None:
    raw = {
        "before-install": "a.py",
        "after-install": "b.py",
        "before-uninstall": "c.py",
        "after-uninstall": "d.py",
        "healthcheck": "h.py",
    }
    s = SetupConfig.model_validate(raw)
    assert s.before_install == "a.py"
    assert s.after_install == "b.py"
    assert s.before_uninstall == "c.py"
    assert s.after_uninstall == "d.py"
    assert s.healthcheck == "h.py"


def test_extension_config_schema_alias_and_collections() -> None:
    d = {
        "name": "x",
        "version": "1",
        "schema": 1,
        "agent-ignore": ["p/**"],
        "git-ignore": ["cache/**"],
        "skills": {},
        "files": {},
        "folders": {},
    }
    c = ExtensionConfig.model_validate(d)
    assert c.schema_version == 1
    assert c.agent_ignore == ["p/**"]
    assert c.git_ignore == ["cache/**"]
    assert c.skills == {}
    assert c.setup is None


def test_extension_folder_invalid_mode() -> None:
    with pytest.raises(ValidationError):
        ExtensionFolderEntry(mode="floating")  # type: ignore[arg-type]


def test_core_config_agent_ignore_alias() -> None:
    c = CoreConfig.model_validate({"version": "0.2", "agent-ignore": ["spawn/.extend/**"]})
    assert c.agent_ignore == ["spawn/.extend/**"]


def test_ide_list_default_empty() -> None:
    m = IdeList.model_validate({})
    assert m.ides == []


def test_source_yaml_nested() -> None:
    raw = {
        "extension": "e",
        "source": {"type": "git", "path": "https://example.com/r.git"},
        "installed": {"version": "1.0.0", "installedAt": "2020-01-01"},
    }
    sy = SourceYaml.model_validate(raw)
    assert sy.extension == "e"
    assert sy.source.type == "git"
    assert sy.installed.version == "1.0.0"


def test_source_yaml_optional_branch() -> None:
    raw = {
        "extension": "e",
        "source": {"type": "path", "path": "/x", "branch": "main"},
        "installed": {"version": "1", "installedAt": "t"},
    }
    sy = SourceYaml.model_validate(raw)
    assert sy.source.branch == "main"


def test_extension_hints_global_local_aliases() -> None:
    h = ExtensionHints.model_validate({"global": [" one ", "two"], "local": ["skill-only"]})
    assert h.global_ == [" one ", "two"]
    assert h.local == ["skill-only"]


def test_extension_hints_rejects_non_string_entries() -> None:
    with pytest.raises(ValidationError):
        ExtensionHints.model_validate({"global": [1, "ok"], "local": []})
