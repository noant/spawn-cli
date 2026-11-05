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
from spawn_cli.io.json_io import save_json
from spawn_cli.io.paths import ensure_dir, safe_path
from spawn_cli.io.yaml_io import load_yaml, save_yaml
from spawn_cli.log import get_logger
from spawn_cli.models.config import ExtensionConfig, ReadFlag, SetupConfig

SPAWN_ENTRY_POINT_PROMPT = """\
Before working, read `spawn/navigation.yaml`.
Read every file listed under `read-required`.
Inspect `read-contextual` descriptions and read only files relevant to the current task.
"""

MCP_MERGED_NOTICE = (
    "MCP was merged for this workspace; you may need to press Enable in your IDE MCP UI."
)

CONFIG_FILENAME = "config.yaml"


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
    """Merged extension ``agent-ignore`` only, omitting *skip_ext*."""
    merged: list[str] = []
    seen: set[str] = set()
    for ext in ll.list_extensions(target_root):
        if ext == skip_ext:
            continue
        for g in ll.get_ext_agent_ignore(target_root, ext):
            if g not in seen:
                seen.add(g)
                merged.append(g)
    return merged


def _sync_project_agent_ignore_permissions(target_root: Path, ide: str) -> None:
    old = ll.get_agent_ignore_list(target_root, ide)
    new = ll.get_all_agent_ignore(target_root)
    adapter = ide_get(ide)
    to_remove = sorted(set(old) - set(new))
    to_add = sorted(set(new) - set(old))
    if to_remove:
        adapter.remove_agent_ignore(target_root, to_remove)
    if to_add:
        adapter.add_agent_ignore(target_root, to_add)
    ll.save_agent_ignore_list(target_root, ide, new)


def refresh_core_agent_ignore(target_root: Path, ide: str) -> None:
    _require_init(target_root)
    adapter = ide_get(ide)
    cap = adapter.detect(target_root).capabilities.agent_ignore
    core = ll.get_core_agent_ignore(target_root)
    if cap == "native":
        adapter.rewrite_core_agent_ignore(target_root, core)
    elif cap == "project":
        _sync_project_agent_ignore_permissions(target_root, ide)


def refresh_extension_agent_ignore(target_root: Path, ide: str) -> None:
    _require_init(target_root)
    adapter = ide_get(ide)
    cap = adapter.detect(target_root).capabilities.agent_ignore
    ext = ll.get_merged_extension_agent_ignore(target_root)
    if cap == "native":
        adapter.rewrite_extension_agent_ignore(target_root, ext)
        ll.save_agent_ignore_list(target_root, ide, ext)
    elif cap == "project":
        _sync_project_agent_ignore_permissions(target_root, ide)


def refresh_agent_ignore(target_root: Path, ide: str) -> None:
    _require_init(target_root)
    refresh_core_agent_ignore(target_root, ide)
    refresh_extension_agent_ignore(target_root, ide)


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
        get_logger().info(MCP_MERGED_NOTICE)
    return new_names


def remove_mcp(target_root: Path, ide: str, extension: str) -> None:
    _require_init(target_root)
    names = ll.get_rendered_mcp(target_root, ide, extension)
    ide_get(ide).remove_mcp(target_root, names)
    ll.save_mcp_rendered(target_root, ide, extension, [])


def refresh_entry_point(target_root: Path, ide: str) -> None:
    _require_init(target_root)
    rollup = ll.rollup_hints_for_agents(target_root)
    ll.warn_if_agents_hints_exceed_measurement(rollup)
    if rollup:
        prompt = (
            f"{SPAWN_ENTRY_POINT_PROMPT}\nHints:\n"
            + "\n".join(f"- {h}" for h in rollup)
            + "\n"
        )
    else:
        prompt = SPAWN_ENTRY_POINT_PROMPT
    ide_get(ide).rewrite_entry_point(target_root, prompt)


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
    refresh_navigation(target_root)


def remove_extension_for_ide(target_root: Path, ide: str, extension: str) -> None:
    remove_mcp(target_root, ide, extension)
    remove_skills(target_root, ide, extension)
    new_ext = _agent_ignore_merge_excluding(target_root, extension)
    adapter = ide_get(ide)
    cap = adapter.detect(target_root).capabilities.agent_ignore
    if cap == "native":
        adapter.rewrite_extension_agent_ignore(target_root, new_ext)
        ll.save_agent_ignore_list(target_root, ide, new_ext)
    elif cap == "project":
        desired = ll.merge_core_and_extension_agent_ignore(
            ll.get_core_agent_ignore(target_root), new_ext
        )
        old = ll.get_agent_ignore_list(target_root, ide)
        to_remove = sorted(set(old) - set(desired))
        to_add = sorted(set(desired) - set(old))
        if to_remove:
            adapter.remove_agent_ignore(target_root, to_remove)
        if to_add:
            adapter.add_agent_ignore(target_root, to_add)
        ll.save_agent_ignore_list(target_root, ide, desired)


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


def refresh_repository(target_root: Path) -> None:
    """Overwrite core config from bundled defaults, then rebuild all IDE-facing metadata."""
    _require_init(target_root)
    ll.sync_core_config_from_defaults(target_root)
    needs_skill = _any_extension_has_skill_files(target_root)
    needs_mcp = _any_extension_has_mcp_servers(target_root)
    for ide in ll.list_ides(target_root):
        _warn_capability_gaps(
            ide,
            ide_get(ide).detect(target_root).capabilities,
            needs_skill_render=needs_skill,
            needs_mcp_merge=needs_mcp,
        )
    merged_any = False
    for ide in ll.list_ides(target_root):
        for ext in ll.list_extensions(target_root):
            names = refresh_mcp(target_root, ide, ext, emit_mcp_merged_notice=False)
            if names:
                merged_any = True
        _refresh_skills_all_extensions_for_ide(target_root, ide)
    for ide in ll.list_ides(target_root):
        refresh_agent_ignore(target_root, ide)
    if merged_any:
        get_logger().info(MCP_MERGED_NOTICE)
    refresh_gitignore(target_root)
    refresh_navigation(target_root)
    for ide in ll.list_ides(target_root):
        refresh_entry_point(target_root, ide)


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


def _ensure_empty_mcp_platform_files(extsrc: Path) -> None:
    mdir = extsrc / "mcp"
    ensure_dir(mdir)
    empty: dict = {"servers": []}
    for stem in ("windows", "linux", "macos"):
        p = mdir / f"{stem}.json"
        if not p.is_file():
            save_json(p, empty)


def _resolve_extsrc(path: Path) -> Path:
    if (path / "extsrc" / CONFIG_FILENAME).is_file():
        return path / "extsrc"
    if (path / CONFIG_FILENAME).is_file():
        return path
    raise SpawnError(f"extsrc/{CONFIG_FILENAME} is missing")


def _validate_all_mcp_platform_files(
    paths: list[Path] | tuple[Path, ...],
    cfg: ExtensionConfig,
    strict: bool,
    warnings_out: list[str],
) -> list[frozenset[str]] | None:
    name_sets: list[frozenset[str]] = []
    for p in paths:
        result = _validate_mcp_platform_file(p, cfg, strict, warnings_out, name_sets)
        if result is None:
            return None
        name_sets = result
    return name_sets


def _collect_mcp_warnings(
    extsrc: Path,
    cfg: ExtensionConfig,
    strict: bool,
    warnings_out: list[str],
) -> list[str]:
    root_mcp = extsrc / "mcp.json"
    if root_mcp.is_file():
        msg = (
            "obsolete extsrc/mcp.json is not used; remove it and use "
            "extsrc/mcp/windows.json, linux.json, and macos.json only"
        )
        if strict:
            raise SpawnError(msg)
        warnings_out.append(msg)
    mcp_dir = extsrc / "mcp"
    if not mcp_dir.is_dir():
        msg = "missing extsrc/mcp/ directory (expected windows.json, linux.json, macos.json)"
        if strict:
            raise SpawnError(msg)
        warnings_out.append(msg)
        return warnings_out
    paths = ll.extension_mcp_platform_json_paths(extsrc)
    if not all(p.is_file() for p in paths):
        missing = [p.name for p in paths if not p.is_file()]
        msg = f"incomplete extsrc/mcp layout (missing {', '.join(missing)})"
        if strict:
            raise SpawnError(msg)
        warnings_out.append(msg)
        return warnings_out
    name_sets = _validate_all_mcp_platform_files(paths, cfg, strict, warnings_out)
    if name_sets is None:
        return warnings_out
    if len(set(name_sets)) != 1:
        msg = (
            "MCP server names must match across mcp/windows.json, "
            "linux.json, and macos.json"
        )
        if strict:
            raise SpawnError(msg)
        warnings_out.append(msg)
    return warnings_out


def _validate_mcp_platform_file(
    p: Path,
    cfg: ExtensionConfig,
    strict: bool,
    warnings_out: list[str],
    name_sets: list[frozenset[str]],
) -> list[frozenset[str]] | None:
    try:
        nm = ll.normalized_mcp_from_mcp_json_path(p, cfg.name or "extension")
    except Exception as e:
        if strict:
            raise SpawnError(f"MCP file invalid ({p}): {e}") from e
        warnings_out.append(f"MCP file invalid ({p}): {e}")
        return None
    for srv in nm.servers:
        if srv.spawn_stdio_proxy and srv.transport.type != "stdio":
            msg = (
                f"MCP server {srv.name!r} in {p}: spawn_stdio_proxy requires "
                f"transport.type 'stdio' (got {srv.transport.type!r})"
            )
            if strict:
                raise SpawnError(msg)
            warnings_out.append(msg)
    name_sets.append(frozenset(s.name for s in nm.servers))
    return name_sets


def extension_init(path: Path, name: str) -> None:
    extsrc = path / "extsrc"
    cfg_path = extsrc / CONFIG_FILENAME
    if cfg_path.is_file():
        warnings.warn(
            f"extsrc/{CONFIG_FILENAME} already exists; left unchanged during extension init",
            SpawnWarning,
        )
        return
    ensure_dir(extsrc / "skills")
    ensure_dir(extsrc / "files")
    ensure_dir(extsrc / "setup")
    _ensure_empty_mcp_platform_files(extsrc)
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


def _check_condition(condition: bool, msg: str, strict: bool, warnings_out: list[str]) -> None:
    if condition:
        if strict:
            raise SpawnError(msg)
        warnings_out.append(msg)


def _validate_skills(extsrc: Path, skills: dict, strict: bool, warnings_out: list[str]) -> None:
    skills_dir = extsrc / "skills"
    for key in skills:
        if not (skills_dir / key).is_file():
            _check_condition(True, f"skill file missing: skills/{key}", strict, warnings_out)


def _validate_file_descriptions(files: dict, strict: bool, warnings_out: list[str]) -> None:
    for name, ent in files.items():
        if ent.globalRead != ReadFlag.no or ent.localRead != ReadFlag.no:
            if not ent.description or not ent.description.strip():
                _check_condition(True, f"file {name!r} has read visibility but no description", strict, warnings_out)


def _validate_setup_scripts(setup: SetupConfig | None, setup_dir: Path, strict: bool, warnings_out: list[str]) -> None:
    if not setup:
        return
    for phase, rel in (
        ("before-install", setup.before_install),
        ("after-install", setup.after_install),
        ("before-uninstall", setup.before_uninstall),
        ("after-uninstall", setup.after_uninstall),
        ("healthcheck", setup.healthcheck),
    ):
        if rel and not (setup_dir / rel).is_file():
            _check_condition(True, f"setup script missing: setup/{rel}", strict, warnings_out)


def _validate_declared_files(files_dir: Path, declared: set[str], strict: bool, warnings_out: list[str]) -> None:
    if not files_dir.is_dir():
        return
    for f in files_dir.rglob("*"):
        if f.is_file():
            rel = f.relative_to(files_dir).as_posix()
            if rel not in declared:
                _check_condition(True, f"undeclared file under extsrc/files: {rel}", strict, warnings_out)


def extension_check(path: Path, strict: bool = False) -> list[str]:
    warnings_out: list[str] = []
    extsrc = _resolve_extsrc(path)
    cfg_path = extsrc / CONFIG_FILENAME
    raw = load_yaml(cfg_path)
    try:
        cfg = ExtensionConfig.model_validate(raw)
    except Exception as e:
        raise SpawnError(f"invalid extension config: {e}") from e
    _validate_skills(extsrc, cfg.skills, strict, warnings_out)
    _validate_file_descriptions(cfg.files, strict, warnings_out)
    _collect_mcp_warnings(extsrc, cfg, strict, warnings_out)
    _validate_setup_scripts(cfg.setup, extsrc / "setup", strict, warnings_out)
    _validate_declared_files(extsrc / "files", set(cfg.files.keys()), strict, warnings_out)
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
            extsrc / CONFIG_FILENAME,
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
        _ensure_empty_mcp_platform_files(extsrc)
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
        get_logger().info(MCP_MERGED_NOTICE)
    refresh_agent_ignore(target_root, ide)


def remove_ide(target_root: Path, ide: str) -> None:
    _require_init(target_root)
    for ext in ll.list_extensions(target_root):
        remove_mcp(target_root, ide, ext)
        remove_skills(target_root, ide, ext)
    ide_get(ide).clear_spawn_agent_ignore(target_root)
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
    "refresh_core_agent_ignore",
    "refresh_extension_agent_ignore",
    "refresh_entry_point",
    "refresh_extension",
    "refresh_extension_for_ide",
    "refresh_gitignore",
    "refresh_mcp",
    "refresh_navigation",
    "refresh_repository",
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
