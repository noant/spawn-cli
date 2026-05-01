from __future__ import annotations

import shutil
import tempfile
import warnings
from pathlib import Path

from spawn_cli.core import download as dl
from spawn_cli.core import low_level as ll
from spawn_cli.core import scripts
from spawn_cli.core.errors import SpawnError, SpawnWarning
from spawn_cli.ide.registry import IdeCapabilities, get as ide_get
from spawn_cli.io.json_io import load_json
from spawn_cli.io.paths import ensure_dir, safe_path
from spawn_cli.io.yaml_io import load_yaml, save_yaml
from spawn_cli.models.config import ExtensionConfig, ReadFlag

SPAWN_ENTRY_POINT_PROMPT = """\
Before working, read `spawn/navigation.yaml`.
Read every file listed under `read-required`.
Inspect `read-contextual` descriptions and read only files relevant to the current task.
"""

MCP_MERGED_NOTICE = (
    "MCP was merged for this workspace; you may need to press Enable in your IDE MCP UI."
)


def _any_extension_has_skill_files(target_root: Path) -> bool:
    return any(ll.list_skills(target_root, ext) for ext in ll.list_extensions(target_root))


def _any_extension_has_mcp_servers(target_root: Path) -> bool:
    return any(ll.list_mcp(target_root, ext).servers for ext in ll.list_extensions(target_root))


def _warn_capability_gaps(
    ide_key: str,
    caps: IdeCapabilities,
    *,
    needs_skill_render: bool,
    needs_mcp_merge: bool,
) -> None:
    if needs_skill_render and caps.skills == "unsupported":
        warnings.warn(
            f"IDE {ide_key!r} does not support skills; skills were skipped",
            SpawnWarning,
        )
    if needs_mcp_merge and caps.mcp in ("unsupported", "external"):
        warnings.warn(
            f"IDE {ide_key!r} has limited MCP support ({caps.mcp})",
            SpawnWarning,
        )


def _require_init(target_root: Path) -> None:
    if not (target_root / "spawn").is_dir():
        raise SpawnError("need init before running this command")


def _extend_dir(target_root: Path, extension: str) -> Path:
    return target_root / "spawn" / ".extend" / extension


def _agent_ignore_merge_excluding(target_root: Path, skip_ext: str) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for g in ll.get_core_agent_ignore(target_root):
        if g not in seen:
            seen.add(g)
            merged.append(g)
    for ext in ll.list_extensions(target_root):
        if ext == skip_ext:
            continue
        for g in ll.get_ext_agent_ignore(target_root, ext):
            if g not in seen:
                seen.add(g)
                merged.append(g)
    return merged


def refresh_gitignore(target_root: Path) -> None:
    _require_init(target_root)
    new_items: list[str] = []
    seen: set[str] = set()
    for ext in ll.list_extensions(target_root):
        for g in ll.get_ext_git_ignore(target_root, ext):
            if g not in seen:
                seen.add(g)
                new_items.append(g)
    existing = ll.get_git_ignore_list(target_root)
    ll.save_git_ignore_list(target_root, new_items)
    new_set, ex_set = set(new_items), set(existing)
    ll.push_to_global_gitignore(target_root, sorted(new_set - ex_set))
    ll.remove_from_global_gitignore(target_root, sorted(ex_set - new_set))


def refresh_agent_ignore(target_root: Path, ide: str) -> None:
    _require_init(target_root)
    old = ll.get_agent_ignore_list(target_root, ide)
    new = ll.get_all_agent_ignore(target_root)
    adapter = ide_get(ide)
    adapter.remove_agent_ignore(target_root, sorted(set(old) - set(new)))
    adapter.add_agent_ignore(target_root, sorted(set(new) - set(old)))
    ll.save_agent_ignore_list(target_root, ide, new)


def refresh_skills(target_root: Path, ide: str, extension: str) -> None:
    _require_init(target_root)
    adapter = ide_get(ide)
    prior = ll.get_rendered_skills(target_root, ide, extension)
    ll.validate_rendered_identity(target_root)
    adapter.remove_skills(target_root, prior)
    metas = ll.generate_skills_metadata(target_root, extension)
    rendered = adapter.add_skills(target_root, metas)
    ll.save_skills_rendered(target_root, ide, extension, rendered)


def _refresh_skills_all_extensions_for_ide(target_root: Path, ide: str) -> None:
    """Re-render every extension's skills on *ide*.

    Skill metadata merges global reads from all installed extensions; peers must
    be rebuilt when any extension's global read set changes.
    """
    for ext in ll.list_extensions(target_root):
        refresh_skills(target_root, ide, ext)


def remove_skills(target_root: Path, ide: str, extension: str) -> None:
    _require_init(target_root)
    prior = ll.get_rendered_skills(target_root, ide, extension)
    ide_get(ide).remove_skills(target_root, prior)
    ll.save_skills_rendered(target_root, ide, extension, [])


def refresh_mcp(
    target_root: Path,
    ide: str,
    extension: str,
    *,
    emit_mcp_merged_notice: bool = True,
) -> list[str]:
    """Merge extension MCP into the IDE project config.

    Persisted rendered server names from ``adapter.add_mcp`` are returned.
    When ``emit_mcp_merged_notice`` is true and that list is non-empty, prints
    ``MCP_MERGED_NOTICE`` once to stdout (callers that batch refreshes, e.g.
    ``add_ide``, should pass ``emit_mcp_merged_notice=False`` and print once).
    """
    _require_init(target_root)
    prior = ll.get_rendered_mcp(target_root, ide, extension)
    ll.validate_rendered_identity(target_root)
    nm = ll.list_mcp(target_root, extension)
    adapter = ide_get(ide)
    adapter.remove_mcp(target_root, prior)
    new_names = adapter.add_mcp(target_root, nm)
    ll.save_mcp_rendered(target_root, ide, extension, new_names)
    if new_names and emit_mcp_merged_notice:
        print(MCP_MERGED_NOTICE)
    return new_names


def remove_mcp(target_root: Path, ide: str, extension: str) -> None:
    _require_init(target_root)
    names = ll.get_rendered_mcp(target_root, ide, extension)
    ide_get(ide).remove_mcp(target_root, names)
    ll.save_mcp_rendered(target_root, ide, extension, [])


def refresh_entry_point(target_root: Path, ide: str) -> None:
    _require_init(target_root)
    ide_get(ide).rewrite_entry_point(target_root, SPAWN_ENTRY_POINT_PROMPT)


def refresh_extension_for_ide(target_root: Path, ide: str, extension: str) -> None:
    """Merge *extension* MCP on *ide* and re-render skills for every extension.

    Mandatory reads in rendered skills are merged from all extensions'
    ``globalRead`` metadata, so updating one extension can require re-rendering
    skills owned by other extensions even when only this extension's MCP changed.
    """
    needs_skill = _any_extension_has_skill_files(target_root)
    needs_mcp = bool(ll.list_mcp(target_root, extension).servers)
    adapter = ide_get(ide)
    dr = adapter.detect(target_root)
    _warn_capability_gaps(
        ide,
        dr.capabilities,
        needs_skill_render=needs_skill,
        needs_mcp_merge=needs_mcp,
    )
    refresh_mcp(target_root, ide, extension)
    _refresh_skills_all_extensions_for_ide(target_root, ide)
    refresh_agent_ignore(target_root, ide)


def remove_extension_for_ide(target_root: Path, ide: str, extension: str) -> None:
    remove_mcp(target_root, ide, extension)
    remove_skills(target_root, ide, extension)
    old = ll.get_agent_ignore_list(target_root, ide)
    new = _agent_ignore_merge_excluding(target_root, extension)
    adapter = ide_get(ide)
    adapter.remove_agent_ignore(target_root, sorted(set(old) - set(new)))
    adapter.add_agent_ignore(target_root, sorted(set(new) - set(old)))
    ll.save_agent_ignore_list(target_root, ide, new)


def refresh_navigation(target_root: Path) -> None:
    _require_init(target_root)
    for ext in ll.list_extensions(target_root):
        ll.save_extension_navigation(
            target_root,
            ext,
            ll.get_required_read_global(target_root, ext),
            ll.get_auto_read_global(target_root, ext),
        )
    ll.save_rules_navigation(target_root)


def refresh_rules_navigation(target_root: Path) -> None:
    _require_init(target_root)
    ll.save_rules_navigation(target_root)


def _refresh_extension_core(target_root: Path, extension: str) -> None:
    needs_skill = _any_extension_has_skill_files(target_root)
    needs_mcp = bool(ll.list_mcp(target_root, extension).servers)
    for ide in ll.list_ides(target_root):
        adapter = ide_get(ide)
        _warn_capability_gaps(
            ide,
            adapter.detect(target_root).capabilities,
            needs_skill_render=needs_skill,
            needs_mcp_merge=needs_mcp,
        )
    for ide in ll.list_ides(target_root):
        refresh_mcp(target_root, ide, extension)
        _refresh_skills_all_extensions_for_ide(target_root, ide)
    for ide in ll.list_ides(target_root):
        refresh_agent_ignore(target_root, ide)
    refresh_gitignore(target_root)
    refresh_navigation(target_root)
    for ide in ll.list_ides(target_root):
        refresh_entry_point(target_root, ide)


def refresh_extension(target_root: Path, extension: str) -> None:
    _require_init(target_root)
    scripts.run_before_install_scripts(target_root, extension)
    _refresh_extension_core(target_root, extension)
    scripts.run_after_install_scripts(target_root, extension)


def remove_extension(target_root: Path, extension: str) -> None:
    _require_init(target_root)
    if extension not in ll.list_extensions(target_root):
        return
    cfg = ll._load_ext_config(target_root, extension)
    scripts.run_before_uninstall_scripts(target_root, extension)
    for ide in ll.list_ides(target_root):
        remove_extension_for_ide(target_root, ide, extension)
    static_files, static_folders = ll.get_removable(target_root, extension)
    for rel in static_files:
        p = safe_path(target_root, rel.replace("\\", "/"))
        if p.is_file():
            p.unlink(missing_ok=True)
    for rel in static_folders:
        p = safe_path(target_root, rel.replace("\\", "/"))
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
    ext_dir = _extend_dir(target_root, extension)
    after_spec = scripts.snapshot_after_uninstall_script(ext_dir, cfg)
    if ext_dir.is_dir():
        shutil.rmtree(ext_dir, ignore_errors=True)
    refresh_gitignore(target_root)
    refresh_navigation(target_root)
    for ide in ll.list_ides(target_root):
        refresh_agent_ignore(target_root, ide)
        refresh_entry_point(target_root, ide)
    for ide in ll.list_ides(target_root):
        _refresh_skills_all_extensions_for_ide(target_root, ide)
    scripts.run_after_uninstall_from_snapshot(target_root, extension, after_spec)


def update_extension(target_root: Path, extension: str, *, force: bool = False) -> None:
    _require_init(target_root)
    stored = dl._load_stored_source(target_root, extension)
    if not stored:
        raise SpawnError(f"no source.yaml for extension {extension!r}")
    staged = dl._stage_extension(target_root, stored.source.path, stored.source.branch, require_init=True)
    try:
        cand = staged.config
        if dl._source_info_key(staged.source_info) != dl._source_info_key(stored.source):
            raise SpawnError(
                "source identity does not match installed record; remove the extension then install again"
            )
        if not force and dl.compare_version_strings(cand.version, stored.installed.version) <= 0:
            raise SpawnError(
                f"extension version must be newer than installed {stored.installed.version!r} "
                f"(got {cand.version!r})"
            )
        dl._validate_render_identity_for_new_extension(target_root, extension, staged.extsrc_dir)
        scripts.run_before_install_scripts(target_root, extension, ext_layout=staged.extsrc_dir)
        dest = _extend_dir(target_root, extension)
        ensure_dir(dest.parent)
        dl._copy_extsrc_tree(staged.extsrc_dir, dest)
        dl._write_source_yaml(target_root, extension, staged.source_info, cand.version)
        dl._materialize_files(target_root, extension, cand)
    finally:
        staged.cleanup()
    _refresh_extension_core(target_root, extension)
    scripts.run_after_install_scripts(target_root, extension)


def reinstall_extension(target_root: Path, extension: str) -> None:
    _require_init(target_root)
    if extension not in ll.list_extensions(target_root):
        raise SpawnError(f"extension {extension!r} is not installed")
    stored = dl._load_stored_source(target_root, extension)
    if not stored:
        raise SpawnError(f"no source.yaml for extension {extension!r}")
    remove_extension(target_root, extension)
    install_extension(target_root, stored.source.path, stored.source.branch)


def extension_healthcheck(target_root: Path, extension: str) -> bool:
    _require_init(target_root)
    if extension not in ll.list_extensions(target_root):
        return False
    ext_root = _extend_dir(target_root, extension)
    try:
        extension_check(ext_root, strict=True)
    except SpawnError:
        return False
    return scripts.run_healthcheck_scripts(target_root, extension)


def extension_init(path: Path, name: str) -> None:
    extsrc = path / "extsrc"
    cfg_path = extsrc / "config.yaml"
    if cfg_path.is_file():
        warnings.warn(
            "extsrc/config.yaml already exists; left unchanged during extension init",
            SpawnWarning,
        )
        return
    ensure_dir(extsrc / "skills")
    ensure_dir(extsrc / "files")
    ensure_dir(extsrc / "setup")
    template = {
        "name": name,
        "schema": 1,
        "version": "0.1.0",
        "files": {},
        "folders": {},
        "agent-ignore": [],
        "git-ignore": [],
        "skills": {},
        "setup": {},
    }
    save_yaml(cfg_path, template)


def extension_check(path: Path, strict: bool = False) -> list[str]:
    warnings_out: list[str] = []
    if (path / "extsrc" / "config.yaml").is_file():
        extsrc = path / "extsrc"
    elif (path / "config.yaml").is_file():
        extsrc = path
    else:
        raise SpawnError("extsrc/config.yaml is missing")
    cfg_path = extsrc / "config.yaml"
    raw = load_yaml(cfg_path)
    try:
        cfg = ExtensionConfig.model_validate(raw)
    except Exception as e:
        raise SpawnError(f"invalid extension config: {e}") from e
    skills_dir = extsrc / "skills"
    setup_dir = extsrc / "setup"
    files_dir = extsrc / "files"
    for key, sk in cfg.skills.items():
        skill_file = skills_dir / key
        if not skill_file.is_file():
            msg = f"skill file missing: skills/{key}"
            if strict:
                raise SpawnError(msg)
            warnings_out.append(msg)
    for _ent_key, ent in cfg.files.items():
        gr, lr = ent.globalRead, ent.localRead
        if gr != ReadFlag.no or lr != ReadFlag.no:
            if not ent.description or not ent.description.strip():
                msg = f"file {_ent_key!r} has read visibility but no description"
                if strict:
                    raise SpawnError(msg)
                warnings_out.append(msg)
    mcp_path = extsrc / "mcp.json"
    if mcp_path.is_file():
        try:
            load_json(mcp_path)
        except Exception as e:
            msg = f"mcp.json not parseable: {e}"
            if strict:
                raise SpawnError(msg) from e
            warnings_out.append(msg)
    if cfg.setup:
        for _phase, rel in (
            ("before-install", cfg.setup.before_install),
            ("after-install", cfg.setup.after_install),
            ("before-uninstall", cfg.setup.before_uninstall),
            ("after-uninstall", cfg.setup.after_uninstall),
            ("healthcheck", cfg.setup.healthcheck),
        ):
            if rel and not (setup_dir / rel).is_file():
                msg = f"setup script missing: setup/{rel}"
                if strict:
                    raise SpawnError(msg)
                warnings_out.append(msg)
    declared = set(cfg.files.keys())
    if files_dir.is_dir():
        for f in files_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(files_dir).as_posix()
                if rel not in declared:
                    msg = f"undeclared file under extsrc/files: {rel}"
                    if strict:
                        raise SpawnError(msg)
                    warnings_out.append(msg)
    return warnings_out


def extension_from_rules(source: str, output_path: Path, name: str, branch: str | None = None) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="spawn-from-rules-"))
    try:
        src_path = Path(source).expanduser()
        if src_path.is_dir() and (src_path.resolve() / "spawn" / "rules").is_dir():
            root = src_path.resolve()
        else:
            root = dl.stage_repository_root(str(source), branch, tmp)
        rules = root / "spawn" / "rules"
        extsrc = output_path / "extsrc"
        ensure_dir(extsrc / "files" / "spawn" / "rules")
        if rules.is_dir():
            for f in rules.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(rules)
                    dest = extsrc / "files" / "spawn" / "rules" / rel
                    ensure_dir(dest.parent)
                    shutil.copy2(f, dest)
        files_meta: dict = {}
        if rules.is_dir():
            for f in sorted(rules.rglob("*")):
                if f.is_file():
                    rel_key = ("spawn/rules/" + f.relative_to(rules).as_posix()).replace("\\", "/")
                    files_meta[rel_key] = {
                        "description": "Rule imported by extension_from_rules.",
                        "mode": "static",
                        "globalRead": "required",
                        "localRead": "no",
                    }
        save_yaml(
            extsrc / "config.yaml",
            {
                "name": name,
                "schema": 1,
                "version": "0.1.0",
                "files": files_meta,
                "folders": {},
                "agent-ignore": [],
                "git-ignore": [],
                "skills": {},
                "setup": {},
            },
        )
        ensure_dir(extsrc / "skills")
        ensure_dir(extsrc / "setup")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def add_ide(target_root: Path, ide: str) -> None:
    _require_init(target_root)
    ll.add_ide_to_list(target_root, ide)
    adapter = ide_get(ide)
    dr = adapter.detect(target_root)
    _warn_capability_gaps(
        ide,
        dr.capabilities,
        needs_skill_render=_any_extension_has_skill_files(target_root),
        needs_mcp_merge=_any_extension_has_mcp_servers(target_root),
    )
    refresh_entry_point(target_root, ide)
    merged_any = False
    for ext in ll.list_extensions(target_root):
        new_names = refresh_mcp(target_root, ide, ext, emit_mcp_merged_notice=False)
        if new_names:
            merged_any = True
    _refresh_skills_all_extensions_for_ide(target_root, ide)
    if merged_any:
        print(MCP_MERGED_NOTICE)
    refresh_agent_ignore(target_root, ide)


def remove_ide(target_root: Path, ide: str) -> None:
    _require_init(target_root)
    for ext in ll.list_extensions(target_root):
        remove_mcp(target_root, ide, ext)
        remove_skills(target_root, ide, ext)
    old = ll.get_agent_ignore_list(target_root, ide)
    ide_get(ide).remove_agent_ignore(target_root, old)
    ide_get(ide).finalize_repo_after_ide_removed(target_root)
    ll.remove_ide_from_list(target_root, ide)
    ll.remove_ide_metadata_dir(target_root, ide)


def install_extension(target_root: Path, path: str, branch: str | None = None) -> None:
    _require_init(target_root)
    name = dl.download_extension(target_root, path, branch)
    _refresh_extension_core(target_root, name)
    scripts.run_after_install_scripts(target_root, name)


__all__ = [
    "MCP_MERGED_NOTICE",
    "SPAWN_ENTRY_POINT_PROMPT",
    "_refresh_extension_core",
    "add_ide",
    "extension_check",
    "extension_from_rules",
    "extension_healthcheck",
    "extension_init",
    "install_extension",
    "refresh_agent_ignore",
    "refresh_entry_point",
    "refresh_extension",
    "refresh_extension_for_ide",
    "refresh_gitignore",
    "refresh_mcp",
    "refresh_navigation",
    "refresh_rules_navigation",
    "refresh_skills",
    "reinstall_extension",
    "remove_extension",
    "remove_extension_for_ide",
    "remove_ide",
    "remove_mcp",
    "remove_skills",
    "update_extension",
]
