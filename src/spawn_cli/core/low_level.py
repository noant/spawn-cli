from __future__ import annotations

import re
import shutil
import time
import uuid
import warnings
from collections import defaultdict
from collections.abc import Iterable
from importlib import resources
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from spawn_cli.core.errors import SpawnError, SpawnWarning
from spawn_cli.io.json_io import load_json
from spawn_cli.io.paths import ensure_dir
from spawn_cli.io.text_io import read_lines, write_lines
from spawn_cli.io.yaml_io import configure_yaml_dump, load_yaml, save_yaml
from spawn_cli.models.config import CoreConfig, ExtensionConfig, FileMode, IdeList, ReadFlag
from spawn_cli.models.mcp import McpCapabilities, McpEnvVar, McpServer, McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillFileRef, SkillMetadata, SkillRawInfo

CANONICAL_IDE_KEYS: tuple[str, ...] = (
    "cursor",
    "codex",
    "claude-code",
    "windsurf",
    "github-copilot",
    "gemini-cli",
)

SPAWN_GITIGNORE_START = "# spawn:start"
SPAWN_GITIGNORE_END = "# spawn:end"


def _spawn(root: Path) -> Path:
    return root / "spawn"


def _extend_root(root: Path) -> Path:
    return _spawn(root) / ".extend"


def supported_ide_keys() -> list[str]:
    return list(CANONICAL_IDE_KEYS)


def normalize_skill_name(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"[^a-z0-9._-]", "", name)
    name = re.sub(r"-{2,}", "-", name)
    return name


def list_extensions(target_root: Path) -> list[str]:
    p = _extend_root(target_root)
    if not p.is_dir():
        return []
    return sorted(d.name for d in p.iterdir() if d.is_dir())


def list_ides(target_root: Path) -> list[str]:
    path = _spawn(target_root) / ".metadata" / "ide.yaml"
    data = load_yaml(path)
    model = IdeList.model_validate(data) if data else IdeList()
    return list(model.ides)


def add_ide_to_list(target_root: Path, ide: str) -> None:
    path = _spawn(target_root) / ".metadata" / "ide.yaml"
    data = load_yaml(path)
    model = IdeList.model_validate(data) if data else IdeList()
    if ide not in model.ides:
        model.ides.append(ide)
    save_yaml(path, model.model_dump(by_alias=True, exclude_none=True))


def remove_ide_from_list(target_root: Path, ide: str) -> None:
    path = _spawn(target_root) / ".metadata" / "ide.yaml"
    data = load_yaml(path)
    model = IdeList.model_validate(data) if data else IdeList()
    model.ides = [x for x in model.ides if x != ide]
    save_yaml(path, model.model_dump(by_alias=True, exclude_none=True))


METADATA_TEMP_MAX_AGE_SECONDS = 86400


def remove_ide_metadata_dir(target_root: Path, ide: str) -> None:
    md = _spawn(target_root) / ".metadata" / ide
    if md.is_dir():
        shutil.rmtree(md, ignore_errors=True)


def prune_metadata_temp(parent: Path, *, max_age_seconds: int, reserved: str | None = None) -> None:
    if not parent.is_dir():
        return
    now = time.time()
    for child in sorted(parent.iterdir(), key=lambda p: p.name):
        try:
            if not child.is_dir():
                continue
            uuid.UUID(child.name)
        except ValueError:
            continue
        except OSError:
            continue
        if reserved and child.name == reserved:
            continue
        try:
            age = now - child.stat().st_mtime
            if age > max_age_seconds:
                shutil.rmtree(child, ignore_errors=True)
        except OSError:
            continue


def _config_path(target_root: Path, extension: str) -> Path:
    return _extend_root(target_root) / extension / "config.yaml"


def _load_ext_config(target_root: Path, extension: str) -> ExtensionConfig:
    path = _config_path(target_root, extension)
    raw = load_yaml(path)
    if not raw:
        raise SpawnError(f"missing extension config: {extension!r}")
    return ExtensionConfig.model_validate(raw)


def _file_refs_for_global(extension: ExtensionConfig, flag_required: bool) -> list[SkillFileRef]:
    out: list[SkillFileRef] = []
    for path_str, ent in extension.files.items():
        if flag_required:
            if ent.globalRead != ReadFlag.required:
                continue
        else:
            if ent.globalRead != ReadFlag.auto:
                continue
        desc = ent.description or ""
        out.append(SkillFileRef(file=path_str, description=desc))
    return out


def _file_refs_for_local(extension: ExtensionConfig, flag_required: bool) -> list[SkillFileRef]:
    out: list[SkillFileRef] = []
    for path_str, ent in extension.files.items():
        if flag_required:
            if ent.localRead != ReadFlag.required:
                continue
        else:
            if ent.localRead != ReadFlag.auto:
                continue
        desc = ent.description or ""
        out.append(SkillFileRef(file=path_str, description=desc))
    return out


def get_required_read_global(target_root: Path, extension: str) -> list[SkillFileRef]:
    cfg = _load_ext_config(target_root, extension)
    return _file_refs_for_global(cfg, True)


def get_required_read_global_all(target_root: Path) -> dict[str, list[SkillFileRef]]:
    return {
        ext: get_required_read_global(target_root, ext)
        for ext in list_extensions(target_root)
    }


def get_required_read_ext_local(target_root: Path, extension: str) -> list[SkillFileRef]:
    cfg = _load_ext_config(target_root, extension)
    return _file_refs_for_local(cfg, True)


def get_auto_read_global(target_root: Path, extension: str) -> list[SkillFileRef]:
    cfg = _load_ext_config(target_root, extension)
    return _file_refs_for_global(cfg, False)


def get_auto_read_global_all(target_root: Path) -> dict[str, list[SkillFileRef]]:
    return {
        ext: get_auto_read_global(target_root, ext)
        for ext in list_extensions(target_root)
    }


def get_auto_read_local(target_root: Path, extension: str) -> list[SkillFileRef]:
    cfg = _load_ext_config(target_root, extension)
    return _file_refs_for_local(cfg, False)


def get_folders(target_root: Path, extension: str) -> dict[str, Any]:
    cfg = _load_ext_config(target_root, extension)
    return {k: v.model_dump(by_alias=True) for k, v in cfg.folders.items()}


def get_removable(target_root: Path, extension: str) -> tuple[list[str], list[str]]:
    cfg = _load_ext_config(target_root, extension)
    static_files: list[str] = []
    static_folders: list[str] = []
    for p, ent in cfg.files.items():
        if ent.mode == FileMode.static:
            static_files.append(p)
    for folder, ent in cfg.folders.items():
        if ent.mode == FileMode.static:
            static_folders.append(folder)
    return static_files, static_folders


def list_skills(target_root: Path, extension: str) -> list[Path]:
    root = _extend_root(target_root) / extension / "skills"
    if not root.is_dir():
        return []
    return sorted(p for p in root.glob("*.md") if p.is_file())


def _parse_frontmatter(body: str) -> tuple[dict[str, Any], str]:
    lines = body.splitlines(True)
    if not lines:
        return {}, body
    if lines[0].strip() != "---":
        return {}, body
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, body
    fm_yaml = "".join(lines[1:end])
    remainder = "".join(lines[end + 1 :])
    yaml = YAML(typ="safe")
    meta = yaml.load(fm_yaml)
    meta_dict = meta if isinstance(meta, dict) else {}
    return meta_dict, remainder


def _describe_path(cfg: ExtensionConfig, path_str: str) -> str:
    ent = cfg.files.get(path_str)
    return ent.description or "" if ent else ""


def get_skill_raw_info(target_root: Path, extension: str, skill_path: Path) -> SkillRawInfo:
    cfg = _load_ext_config(target_root, extension)
    text = skill_path.read_text(encoding="utf-8")
    fm, content = _parse_frontmatter(text)
    key = skill_path.name
    sk_entry = cfg.skills.get(key)
    fm_name = fm.get("name")
    fm_desc = fm.get("description")
    name: str
    if sk_entry and sk_entry.name:
        name = sk_entry.name
    elif fm_name is not None:
        name = str(fm_name)
    else:
        name = key.replace(".md", "")
    description = ""
    if sk_entry and sk_entry.description:
        description = sk_entry.description
    elif fm_desc is not None:
        description = str(fm_desc)
    req_read: list[str] = []
    if sk_entry and sk_entry.required_read:
        req_read = list(sk_entry.required_read)
    return SkillRawInfo(
        name=name,
        description=description,
        content=content,
        required_read=req_read,
    )


def _flatten_global_refs_ordered(
    target_root: Path, per_ext: dict[str, list[SkillFileRef]]
) -> list[SkillFileRef]:
    out: list[SkillFileRef] = []
    seen: set[str] = set()
    for ext_id in list_extensions(target_root):
        for ref in per_ext.get(ext_id, []):
            nk = _norm_read_path(ref.file)
            if nk in seen:
                continue
            seen.add(nk)
            out.append(ref)
    return out


def _norm_read_path(path_str: str) -> str:
    """Normalize relative paths when comparing skill required vs contextual lists."""
    return Path(path_str).as_posix().replace("\\", "/")


def _navigation_rules_refs_from_section(section: Any) -> list[SkillFileRef]:
    out: list[SkillFileRef] = []
    if not isinstance(section, list):
        return out
    for grp in section:
        if not isinstance(grp, dict):
            continue
        rules_raw = grp.get("rules")
        if not isinstance(rules_raw, list):
            continue
        for entry in rules_raw:
            if not isinstance(entry, dict):
                continue
            path_raw = entry.get("path")
            if not isinstance(path_raw, str) or not path_raw.strip():
                continue
            desc_raw = entry.get("description")
            desc = "" if desc_raw is None else str(desc_raw)
            out.append(SkillFileRef(file=path_raw.strip(), description=desc))
    return out


def _navigation_yaml_rules_refs(target_root: Path) -> tuple[list[SkillFileRef], list[SkillFileRef]]:
    """Return (read-required rules, read-contextual rules) from merged navigation.yaml."""
    path = _spawn(target_root) / "navigation.yaml"
    raw = load_yaml(path)
    if not isinstance(raw, dict):
        return [], []
    rr = raw.get("read-required")
    cq = raw.get("read-contextual")
    return (
        _navigation_rules_refs_from_section(rr if isinstance(rr, list) else []),
        _navigation_rules_refs_from_section(cq if isinstance(cq, list) else []),
    )


def _required_read_description_for_path(
    p: str,
    merged_global: list[SkillFileRef],
    local_req: list[SkillFileRef],
    cfg_ext: ExtensionConfig,
    nav_rules_required: list[SkillFileRef] | None = None,
) -> str:
    nk = _norm_read_path(p)
    if nav_rules_required:
        for r in nav_rules_required:
            if _norm_read_path(r.file) == nk and r.description:
                return r.description
    for r in merged_global:
        if _norm_read_path(r.file) == nk and r.description:
            return r.description
    for r in local_req:
        if _norm_read_path(r.file) == nk and r.description:
            return r.description
    return _describe_path(cfg_ext, p)


def generate_skills_metadata(target_root: Path, extension: str) -> list[SkillMetadata]:
    cfg_ext = _load_ext_config(target_root, extension)
    merged_global_required = _flatten_global_refs_ordered(
        target_root, get_required_read_global_all(target_root)
    )
    merged_global_auto = _flatten_global_refs_ordered(target_root, get_auto_read_global_all(target_root))
    local_required = get_required_read_ext_local(target_root, extension)
    local_auto = get_auto_read_local(target_root, extension)
    nav_rules_required, nav_rules_contextual = _navigation_yaml_rules_refs(target_root)

    metas: list[SkillMetadata] = []
    for skill_path in list_skills(target_root, extension):
        raw = get_skill_raw_info(target_root, extension, skill_path)
        required_paths: list[str] = []
        seen_norm: set[str] = set()
        for blob in (
            list(raw.required_read),
            [r.file for r in local_required],
            [r.file for r in merged_global_required],
        ):
            for fp in blob:
                nk = _norm_read_path(fp)
                if nk in seen_norm:
                    continue
                seen_norm.add(nk)
                required_paths.append(fp)
        for ref in nav_rules_required:
            nk = _norm_read_path(ref.file)
            if nk in seen_norm:
                continue
            seen_norm.add(nk)
            required_paths.append(ref.file)

        required_out = [
            SkillFileRef(
                file=p,
                description=_required_read_description_for_path(
                    p, merged_global_required, local_required, cfg_ext, nav_rules_required
                ),
            )
            for p in required_paths
        ]

        required_key_set = {_norm_read_path(p) for p in required_paths}

        auto_out: list[SkillFileRef] = []
        seen_auto: set[str] = set()
        for ar in local_auto:
            key = _norm_read_path(ar.file)
            if key in required_key_set or key in seen_auto:
                continue
            seen_auto.add(key)
            auto_out.append(ar)
        for ar in merged_global_auto:
            key = _norm_read_path(ar.file)
            if key in required_key_set or key in seen_auto:
                continue
            seen_auto.add(key)
            auto_out.append(ar)
        for ar in nav_rules_contextual:
            key = _norm_read_path(ar.file)
            if key in required_key_set or key in seen_auto:
                continue
            seen_auto.add(key)
            auto_out.append(ar)

        metas.append(
            SkillMetadata(
                name=raw.name,
                description=raw.description,
                content=raw.content,
                required_read=required_out,
                auto_read=auto_out,
            )
        )
    return metas


def validate_rendered_identity(target_root: Path) -> None:
    exts = list_extensions(target_root)
    skill_claims: dict[str, list[str]] = defaultdict(list)
    mcp_claims: dict[str, list[str]] = defaultdict(list)

    for ext in exts:
        for meta in generate_skills_metadata(target_root, ext):
            nk = normalize_skill_name(meta.name)
            skill_claims[nk].append(ext)
        nm = list_mcp(target_root, ext)
        for srv in nm.servers:
            mcp_claims[srv.name].append(ext)

    for key, holders in skill_claims.items():
        if len(holders) > 1:
            uniq = sorted(set(holders))
            raise SpawnError(
                f"duplicate normalized skill names across extensions ({key!r}): extensions {uniq}"
            )
    for srv_name, holders in mcp_claims.items():
        if len(holders) > 1:
            uniq = sorted(set(holders))
            raise SpawnError(
                f"duplicate MCP server names across extensions ({srv_name!r}): extensions {uniq}"
            )


def _parse_mcp_env(env_raw: dict[str, Any]) -> dict[str, McpEnvVar]:
    out: dict[str, McpEnvVar] = {}
    for k, v in env_raw.items():
        if isinstance(v, dict):
            out[str(k)] = McpEnvVar.model_validate(v)
        else:
            out[str(k)] = McpEnvVar(source="user", required=True, secret=True)
    return out


def _mcp_capabilities(raw: dict[str, Any]) -> McpCapabilities:
    c = raw.get("capabilities") or {}
    return McpCapabilities.model_validate(c) if isinstance(c, dict) else McpCapabilities()


def list_mcp(target_root: Path, extension: str) -> NormalizedMcp:
    path = _extend_root(target_root) / extension / "mcp.json"
    data = load_json(path)
    servers_out: list[McpServer] = []
    for s in data.get("servers") or []:
        if not isinstance(s, dict):
            continue
        nm = s.get("name")
        if nm is None:
            raise SpawnError(f"missing MCP server name in {path}")
        tr_raw = s.get("transport") or {}
        transport = McpTransport(
            type=str(tr_raw.get("type", "stdio")),
            command=tr_raw.get("command"),
            args=list(tr_raw.get("args") or []),
            cwd=str(tr_raw.get("cwd", ".")),
            url=tr_raw.get("url"),
        )
        env_in = s.get("env") or {}
        env = _parse_mcp_env(env_in) if isinstance(env_in, dict) else {}
        servers_out.append(
            McpServer(
                name=str(nm),
                extension=extension,
                transport=transport,
                env=env,
                capabilities=_mcp_capabilities(s),
            )
        )
    return NormalizedMcp(servers=servers_out)


def get_navigation_metadata(target_root: Path, extension: str) -> dict:
    return {
        "required": [x.model_dump(by_alias=True) for x in get_required_read_global(target_root, extension)],
        "contextual": [x.model_dump(by_alias=True) for x in get_auto_read_global(target_root, extension)],
    }


def get_core_agent_ignore(target_root: Path) -> list[str]:
    path = _spawn(target_root) / ".core" / "config.yaml"
    data = load_yaml(path)
    if not data:
        return []
    core = CoreConfig.model_validate(data)
    return list(core.agent_ignore)


def sync_core_config_from_defaults(target_root: Path) -> None:
    """Overwrite ``spawn/.core/config.yaml`` with bundled default ``CoreConfig``.

    Validates that an existing repo file parses as ``CoreConfig`` before
    replacing it so corrupted files are not silently clobbered.
    """
    path = _spawn(target_root) / ".core" / "config.yaml"
    if not path.is_file():
        raise SpawnError("spawn/.core/config.yaml is missing; run spawn init.")
    bundled_txt = (
        resources.files("spawn_cli.resources")
        .joinpath("default_core_config.yaml")
        .read_text(encoding="utf-8")
    )
    yparse = YAML(typ="safe")
    raw_default = yparse.load(bundled_txt)
    if not isinstance(raw_default, dict):
        raise SpawnError("internal error: bundled default core config is not a mapping")
    try:
        default_core = CoreConfig.model_validate(raw_default)
    except Exception as e:
        raise SpawnError(f"internal error: bundled default core config invalid: {e}") from e
    raw_existing = load_yaml(path)
    if not raw_existing:
        raise SpawnError(
            "spawn/.core/config.yaml is empty or invalid; restore it or run spawn init again."
        )
    try:
        CoreConfig.model_validate(raw_existing)
    except Exception as e:
        raise SpawnError(f"invalid spawn/.core/config.yaml: {e}") from e
    save_yaml(path, default_core.model_dump(by_alias=True))


def get_ext_agent_ignore(target_root: Path, extension: str) -> list[str]:
    cfg = _load_ext_config(target_root, extension)
    return list(cfg.agent_ignore)


def get_all_agent_ignore(target_root: Path) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for g in get_core_agent_ignore(target_root):
        if g not in seen:
            seen.add(g)
            merged.append(g)
    for ext in list_extensions(target_root):
        for g in get_ext_agent_ignore(target_root, ext):
            if g not in seen:
                seen.add(g)
                merged.append(g)
    return merged


def get_ext_git_ignore(target_root: Path, extension: str) -> list[str]:
    cfg = _load_ext_config(target_root, extension)
    return list(cfg.git_ignore)


def _rendered_skills_path(target_root: Path, ide: str) -> Path:
    return _spawn(target_root) / ".metadata" / ide / "rendered-skills.yaml"


def _rendered_mcp_path(target_root: Path, ide: str) -> Path:
    return _spawn(target_root) / ".metadata" / ide / "rendered-mcp.yaml"


def save_skills_rendered(
    target_root: Path, ide: str, extension: str, skill_paths: list[dict[str, Any]]
) -> None:
    path = _rendered_skills_path(target_root, ide)
    ensure_dir(path.parent)
    data = load_yaml(path) or {}
    exts = dict(data.get("extensions") or {}) if isinstance(data.get("extensions"), dict) else {}
    if not skill_paths:
        exts.pop(extension, None)
    else:
        exts[extension] = list(skill_paths)
    data["extensions"] = exts
    save_yaml(path, data)


def get_rendered_skills(target_root: Path, ide: str, extension: str) -> list[dict]:
    path = _rendered_skills_path(target_root, ide)
    raw = load_yaml(path)
    if not raw:
        return []
    exts = raw.get("extensions") or {}
    if not isinstance(exts, dict):
        return []
    block = exts.get(extension)
    return list(block) if isinstance(block, list) else []


def save_mcp_rendered(target_root: Path, ide: str, extension: str, mcp_names: list[str]) -> None:
    path = _rendered_mcp_path(target_root, ide)
    ensure_dir(path.parent)
    data = load_yaml(path) or {}
    exts = dict(data.get("extensions") or {}) if isinstance(data.get("extensions"), dict) else {}
    if not mcp_names:
        exts.pop(extension, None)
    else:
        exts[extension] = [{"name": n} for n in mcp_names]
    data["extensions"] = exts
    save_yaml(path, data)


def get_rendered_mcp(target_root: Path, ide: str, extension: str) -> list[str]:
    path = _rendered_mcp_path(target_root, ide)
    raw = load_yaml(path)
    if not raw:
        return []
    exts = raw.get("extensions") or {}
    if not isinstance(exts, dict):
        return []
    block = exts.get(extension)
    if not isinstance(block, list):
        return []
    names: list[str] = []
    for item in block:
        if isinstance(item, dict) and "name" in item:
            names.append(str(item["name"]))
        elif isinstance(item, str):
            names.append(item)
    return names


def _git_ignore_list_path(target_root: Path) -> Path:
    return _spawn(target_root) / ".metadata" / "git-ignore.txt"


def get_git_ignore_list(target_root: Path) -> list[str]:
    lines = read_lines(_git_ignore_list_path(target_root))
    return [ln for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]


def save_git_ignore_list(target_root: Path, items: list[str]) -> None:
    write_lines(_git_ignore_list_path(target_root), list(items))


def _agent_ignore_list_path(target_root: Path, ide: str) -> Path:
    return _spawn(target_root) / ".metadata" / ide / "agent-ignore.txt"


def get_agent_ignore_list(target_root: Path, ide: str) -> list[str]:
    lines = read_lines(_agent_ignore_list_path(target_root, ide))
    return [ln for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]


def save_agent_ignore_list(target_root: Path, ide: str, items: list[str]) -> None:
    path = _agent_ignore_list_path(target_root, ide)
    ensure_dir(path.parent)
    write_lines(path, list(items))


def get_global_gitignore(target_root: Path) -> list[str]:
    git_path = target_root / ".gitignore"
    if not git_path.is_file():
        return []
    return read_lines(git_path)


def _partition_gitignore(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    start_idx: int | None = None
    end_idx: int | None = None
    for i, ln in enumerate(lines):
        if ln.strip() == SPAWN_GITIGNORE_START:
            start_idx = i
            break
    if start_idx is None:
        return lines[:], [], []
    for j in range(start_idx + 1, len(lines)):
        if lines[j].strip() == SPAWN_GITIGNORE_END:
            end_idx = j
            break
    if end_idx is None:
        return lines[:start_idx], lines[start_idx + 1 :], []
    return lines[:start_idx], lines[start_idx + 1 : end_idx], lines[end_idx + 1 :]


def push_to_global_gitignore(target_root: Path, items: list[str]) -> None:
    path = target_root / ".gitignore"
    raw = read_lines(path)
    before, interior, after = _partition_gitignore(raw)
    ordered: list[str] = []
    seen: set[str] = set()
    for ln in interior:
        st = ln.strip()
        if not st:
            continue
        if st.startswith("#"):
            continue
        if st not in seen:
            seen.add(st)
            ordered.append(st)
    for it in items:
        st = str(it).strip()
        if st and st not in seen:
            seen.add(st)
            ordered.append(st)
    want_block = bool(ordered)
    new_lines: list[str] = []
    new_lines.extend(before)
    if want_block:
        new_lines.append(SPAWN_GITIGNORE_START)
        new_lines.extend(ordered)
        new_lines.append(SPAWN_GITIGNORE_END)
    new_lines.extend(after)
    ensure_dir(target_root)
    write_lines(path, new_lines)


def remove_from_global_gitignore(target_root: Path, items: list[str]) -> None:
    path = target_root / ".gitignore"
    raw = read_lines(path)
    before, interior, after = _partition_gitignore(raw)
    remove_me = {x.strip() for x in items if x.strip()}
    kept_interior = [
        ln
        for ln in interior
        if not (
            ln.strip()
            and not ln.strip().startswith("#")
            and ln.strip() in remove_me
        )
    ]
    substantive = [
        ln for ln in kept_interior if ln.strip() and not ln.strip().startswith("#")
    ]
    new_lines = list(before)
    if substantive:
        new_lines.append(SPAWN_GITIGNORE_START)
        new_lines.extend(kept_interior)
        new_lines.append(SPAWN_GITIGNORE_END)
    new_lines.extend(after)
    ensure_dir(target_root)
    if raw or new_lines:
        write_lines(path, new_lines)


def _nav_refs_to_files(refs: list[SkillFileRef]) -> list[dict[str, str]]:
    return [{"path": ref.file, "description": ref.description} for ref in refs]


def _strip_ext_sections_inplace(groups: list[Any], extension: str) -> None:
    for i in range(len(groups) - 1, -1, -1):
        item = groups[i]
        if isinstance(item, dict) and item.get("ext") == extension:
            del groups[i]


def _desired_navigation_root_key_order(keys: Iterable[str]) -> list[str]:
    """Canonical top-level navigation keys: read-required, read-contextual, then unknown keys."""

    ks = list(keys)
    others = [k for k in ks if k not in ("read-required", "read-contextual")]
    ordered: list[str] = []
    if "read-required" in ks:
        ordered.append("read-required")
    if "read-contextual" in ks:
        ordered.append("read-contextual")
    ordered.extend(others)
    return ordered


def _ensure_navigation_root_key_order(nav: Any) -> None:
    """Reorder root keys (required before contextual). CommentedMap in-place; plain dict rebuilt."""

    if not isinstance(nav, dict):
        return
    desired = _desired_navigation_root_key_order(nav.keys())
    if list(nav.keys()) == desired:
        return
    mover = getattr(nav, "move_to_end", None)
    if mover is not None:
        for key in reversed(desired):
            if key in nav:
                mover(key, last=False)
        return
    reordered = {k: nav[k] for k in desired}
    nav.clear()
    nav.update(reordered)


def save_extension_navigation(
    target_root: Path,
    extension: str,
    read_required_files: list[SkillFileRef],
    read_contextual_files: list[SkillFileRef],
) -> None:
    nav_path = _spawn(target_root) / "navigation.yaml"
    yaml_rt = YAML(typ="rt")
    configure_yaml_dump(yaml_rt)
    if nav_path.is_file():
        with nav_path.open("r", encoding="utf-8") as fh:
            raw = yaml_rt.load(fh)
    else:
        raw = None
    if raw is None or not isinstance(raw, dict):
        from ruamel.yaml.comments import CommentedMap

        raw = CommentedMap()
    rr = raw.get("read-required")
    if not isinstance(rr, list):
        rr = []
        raw["read-required"] = rr
    rc = raw.get("read-contextual")
    if not isinstance(rc, list):
        rc = []
        raw["read-contextual"] = rc
    _strip_ext_sections_inplace(rr, extension)
    _strip_ext_sections_inplace(rc, extension)
    if read_required_files:
        rr.append({"ext": extension, "files": _nav_refs_to_files(read_required_files)})
    if read_contextual_files:
        req_norm = {_norm_read_path(r.file) for r in read_required_files}
        contextual_only = [
            r for r in read_contextual_files if _norm_read_path(r.file) not in req_norm
        ]
        if contextual_only:
            rc.append({"ext": extension, "files": _nav_refs_to_files(contextual_only)})
    _ensure_navigation_root_key_order(raw)
    ensure_dir(nav_path.parent)
    with nav_path.open("w", encoding="utf-8") as fh:
        yaml_rt.dump(raw, fh)



def save_rules_navigation(target_root: Path) -> None:
    nav_path = _spawn(target_root) / 'navigation.yaml'
    raw = load_yaml(nav_path) or {}
    rr: list[Any] = list(raw['read-required']) if isinstance(raw.get('read-required'), list) else []
    rc: list[Any] = list(raw.get('read-contextual')) if isinstance(raw.get('read-contextual'), list) else []

    rule_dir = _spawn(target_root) / 'rules'
    paths_on_disk: set[str] = set()
    if rule_dir.is_dir():
        for f in sorted(rule_dir.rglob('*')):
            if f.is_file():
                rel_posix = (Path('spawn/rules') / f.relative_to(rule_dir).as_posix()).as_posix()
                paths_on_disk.add(rel_posix.replace('\\', '/'))

    def locate_or_create_rules_list(section: list[Any]) -> list[Any]:
        for grp in section:
            if isinstance(grp, dict) and isinstance(grp.get('rules'), list):
                return grp['rules']
        section.append({'rules': []})
        tail = section[-1]
        if not isinstance(tail, dict):
            raise SpawnError('internal navigation shape error')
        return tail['rules']

    def rule_paths_union(*maybe_lists: list[Any] | None) -> set[str]:
        out: set[str] = set()
        for lst in maybe_lists:
            if not lst:
                continue
            for item in lst:
                if isinstance(item, dict) and 'path' in item:
                    out.add(Path(str(item['path'])).as_posix().replace('\\', '/'))
        return out

    rq_rules_list = locate_or_create_rules_list(rr)

    cq_rules_list: list[Any] | None = None
    for grp in rc:
        if isinstance(grp, dict) and isinstance(grp.get('rules'), list):
            cq_rules_list = grp['rules']
            break

    known_paths = rule_paths_union(rq_rules_list, cq_rules_list)

    for dk in sorted(paths_on_disk):
        if dk not in known_paths:
            rq_rules_list.append({'path': dk, 'description': 'Local rule file.'})

    def posix_norm(p: str) -> str:
        return Path(p).as_posix().replace('\\', '/')

    def prune(lst: list[Any]) -> None:
        out: list[Any] = []
        for entry in lst:
            if not isinstance(entry, dict) or 'path' not in entry:
                continue
            rk = posix_norm(str(entry['path']))
            exists = rk in paths_on_disk and (Path(target_root) / Path(rk)).is_file()
            if exists:
                out.append({'path': rk, 'description': str(entry.get('description') or 'Local rule file.')})
            else:
                warnings.warn(
                    f"Removed missing rule path from navigation: {rk}",
                    SpawnWarning,
                )
        lst[:] = out

    prune(rq_rules_list)
    if cq_rules_list is not None:
        prune(cq_rules_list)

    raw["read-required"] = rr
    raw["read-contextual"] = rc
    _ensure_navigation_root_key_order(raw)
    save_yaml(nav_path, raw)


def init(target_root: Path) -> None:
    s = target_root / 'spawn'
    ensure_dir(s)
    ensure_dir(s / '.core')

    cfg = s / '.core' / 'config.yaml'
    if not cfg.is_file():
        template = resources.files('spawn_cli.resources').joinpath('default_core_config.yaml').read_text(encoding='utf-8')
        cfg.write_text(template, encoding='utf-8')

    md = s / '.metadata'
    ensure_dir(md)

    ide_yaml = md / 'ide.yaml'
    if not ide_yaml.is_file():
        save_yaml(ide_yaml, IdeList().model_dump(by_alias=True, exclude_none=True))

    gif = md / 'git-ignore.txt'
    if not gif.is_file():
        write_lines(gif, [])

    ensure_dir(s / 'rules')

    nav = s / 'navigation.yaml'
    if not nav.is_file():
        save_yaml(nav, {'read-required': [], 'read-contextual': []})

    push_to_global_gitignore(target_root, ["spawn/.metadata/temp/**"])



__all__ = [
    "CANONICAL_IDE_KEYS",
    "add_ide_to_list",
    "generate_skills_metadata",
    "get_agent_ignore_list",
    "get_all_agent_ignore",
    "get_auto_read_global",
    "get_auto_read_global_all",
    "get_auto_read_local",
    "get_core_agent_ignore",
    "get_ext_agent_ignore",
    "get_ext_git_ignore",
    "get_folders",
    "get_git_ignore_list",
    "get_global_gitignore",
    "get_navigation_metadata",
    "get_rendered_mcp",
    "get_rendered_skills",
    "get_removable",
    "get_required_read_ext_local",
    "get_required_read_global",
    "get_required_read_global_all",
    "get_skill_raw_info",
    "init",
    "list_extensions",
    "list_ides",
    "list_mcp",
    "list_skills",
    "sync_core_config_from_defaults",
    "METADATA_TEMP_MAX_AGE_SECONDS",
    "normalize_skill_name",
    "prune_metadata_temp",
    "push_to_global_gitignore",
    "remove_from_global_gitignore",
    "remove_ide_metadata_dir",
    "remove_ide_from_list",
    "save_agent_ignore_list",
    "save_extension_navigation",
    "save_git_ignore_list",
    "save_mcp_rendered",
    "save_rules_navigation",
    "save_skills_rendered",
    "supported_ide_keys",
    "validate_rendered_identity",
]

