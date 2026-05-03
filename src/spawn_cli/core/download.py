from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import uuid
import warnings
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from ruamel.yaml import YAML

from spawn_cli.core import low_level as ll
from spawn_cli.core.errors import SpawnError, SpawnWarning
from spawn_cli.core import scripts
from spawn_cli.io.paths import ensure_dir, safe_path
from spawn_cli.io.yaml_io import load_yaml, save_yaml
from spawn_cli.models.config import ExtensionConfig, ExtensionsMeta, FileMode, SourceYaml

SAFE_YAML = YAML(typ="safe")

GIT_INSTALL_HINT = (
    "Install Git for your OS: Windows (winget install Git.Git), "
    "macOS (brew install git or Xcode CLT), "
    "Linux (sudo apt install git or sudo dnf install git)."
)


def compare_version_strings(a: str, b: str) -> int:
    """Return 1 if a > b, 0 if equal, -1 if a < b.

    Numeric segments (dot-separated leading part) compared left to right as integers.
    Remaining suffix compared lexicographically after numeric parts are tied.
    """

    def split_ver(s: str) -> tuple[list[int], str]:
        s = s.strip()
        m = re.match(r"^((?:\d+\.)*\d+)(.*)$", s)
        if not m:
            return [], s
        num, suf = m.group(1), m.group(2)
        parts = [int(x) for x in num.split(".") if x != ""]
        return parts, suf

    pa, sa = split_ver(a)
    pb, sb = split_ver(b)
    n = max(len(pa), len(pb))
    for i in range(n):
        va = pa[i] if i < len(pa) else 0
        vb = pb[i] if i < len(pb) else 0
        if va < vb:
            return -1
        if va > vb:
            return 1
    if sa < sb:
        return -1
    if sa > sb:
        return 1
    return 0


def _require_init(target_root: Path) -> None:
    if not (target_root / "spawn").is_dir():
        raise SpawnError("need init before running this command")


def _spawn_extend(target_root: Path, ext: str) -> Path:
    return target_root / "spawn" / ".extend" / ext


def _load_installed_config(target_root: Path, ext: str) -> ExtensionConfig:
    raw = load_yaml(_spawn_extend(target_root, ext) / "config.yaml")
    if not raw:
        raise SpawnError(f"missing extension config for {ext!r}")
    return ExtensionConfig.model_validate(raw)


def _parse_frontmatter(body: str) -> tuple[dict[str, Any], str]:
    lines = body.splitlines(True)
    if not lines or lines[0].strip() != "---":
        return {}, body
    end: int | None = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, body
    fm_yaml = "".join(lines[1:end])
    meta = SAFE_YAML.load(fm_yaml)
    meta_dict = meta if isinstance(meta, dict) else {}
    remainder = "".join(lines[end + 1 :])
    return meta_dict, remainder


def _candidate_norm_skill_names(extsrc_dir: Path) -> list[str]:
    raw_cfg = load_yaml(extsrc_dir / "config.yaml")
    if not raw_cfg:
        return []
    cfg = ExtensionConfig.model_validate(raw_cfg)
    skills_dir = extsrc_dir / "skills"
    if not skills_dir.is_dir():
        return []
    norms: list[str] = []
    for skill_path in sorted(p for p in skills_dir.glob("*.md") if p.is_file()):
        key = skill_path.name
        sk = cfg.skills.get(key)
        text = skill_path.read_text(encoding="utf-8")
        fm, _ = _parse_frontmatter(text)
        fm_name = fm.get("name")
        if sk and sk.name:
            name = sk.name
        elif fm_name is not None:
            name = str(fm_name)
        else:
            name = key.replace(".md", "")
        norms.append(ll.normalize_skill_name(name))
    return norms


def _candidate_mcp_server_names(extsrc_dir: Path) -> list[str]:
    return ll.extsrc_mcp_server_names_for_staging(extsrc_dir)


def _validate_render_identity_for_new_extension(target_root: Path, new_name: str, extsrc_dir: Path) -> None:
    skill_claims: dict[str, list[str]] = defaultdict(list)
    mcp_claims: dict[str, list[str]] = defaultdict(list)
    for ext in ll.list_extensions(target_root):
        if ext == new_name:
            continue
        for meta in ll.generate_skills_metadata(target_root, ext):
            skill_claims[ll.normalize_skill_name(meta.name)].append(ext)
        for srv in ll.list_mcp(target_root, ext).servers:
            mcp_claims[srv.name].append(ext)
    for nk in _candidate_norm_skill_names(extsrc_dir):
        skill_claims[nk].append(new_name)
    for nm in _candidate_mcp_server_names(extsrc_dir):
        mcp_claims[nm].append(new_name)
    for key, holders in skill_claims.items():
        if len(set(holders)) > 1:
            raise SpawnError(
                f"duplicate normalized skill names across extensions ({key!r}): extensions {sorted(set(holders))}"
            )
    for srv_name, holders in mcp_claims.items():
        if len(set(holders)) > 1:
            raise SpawnError(
                f"duplicate MCP server names across extensions ({srv_name!r}): extensions {sorted(set(holders))}"
            )


def _check_path_conflicts(target_root: Path, candidate_config: ExtensionConfig, candidate_ext: str) -> None:
    for installed_ext in ll.list_extensions(target_root):
        if installed_ext == candidate_ext:
            continue
        installed_config = _load_installed_config(target_root, installed_ext)
        for file_path in candidate_config.files:
            if file_path in installed_config.files:
                raise SpawnError(f"File conflict: {file_path} claimed by {installed_ext}")
        for folder in candidate_config.folders:
            if folder in installed_config.folders:
                raise SpawnError(f"Folder conflict: {folder} claimed by {installed_ext}")


def _source_info_key(info: SourceYaml.SourceInfo) -> tuple[str, str, str | None]:
    return (info.type, info.path, info.branch)


def _load_stored_source(target_root: Path, ext_name: str) -> SourceYaml | None:
    p = _spawn_extend(target_root, ext_name) / "source.yaml"
    if not p.is_file():
        return None
    raw = load_yaml(p)
    if not raw:
        return None
    return SourceYaml.model_validate(raw)


def _check_install_version_and_source(
    target_root: Path,
    ext_name: str,
    candidate_cfg: ExtensionConfig,
    candidate_source: SourceYaml.SourceInfo,
) -> None:
    stored = _load_stored_source(target_root, ext_name)
    if not stored:
        return
    if _source_info_key(candidate_source) != _source_info_key(stored.source):
        raise SpawnError(
            "source identity does not match installed record; remove the extension then install with the new source"
        )
    if compare_version_strings(candidate_cfg.version, stored.installed.version) <= 0:
        raise SpawnError(
            f"extension version must be newer than installed {stored.installed.version!r} (got {candidate_cfg.version!r})"
        )


def _write_source_yaml(
    target_root: Path,
    ext_name: str,
    source: SourceYaml.SourceInfo,
    installed_version: str,
) -> None:
    path = _spawn_extend(target_root, ext_name) / "source.yaml"
    rec = SourceYaml(
        extension=ext_name,
        source=source,
        installed=SourceYaml.InstalledInfo(
            version=installed_version,
            installedAt=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        ),
    )
    save_yaml(path, rec.model_dump(by_alias=True, exclude_none=True))


def _find_extsrc(local_root: Path) -> Path:
    cand = local_root / "extsrc"
    if (cand / "config.yaml").is_file():
        return cand
    if local_root.name == "extsrc" and (local_root / "config.yaml").is_file():
        return local_root
    raise SpawnError(f"no extsrc/config.yaml under {local_root}")


def _ensure_git() -> None:
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        raise SpawnError(f"git is required for remote extension sources. {GIT_INSTALL_HINT}") from e


def _git_clone(url: str, branch: str | None, dest: Path) -> None:
    _ensure_git()
    cmd = ["git", "clone", "--depth", "1"]
    if branch:
        cmd += ["--branch", branch]
    cmd += [url, str(dest)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SpawnError(f"git clone failed: {(proc.stderr or proc.stdout).strip()}")


def _extract_zip(zpath: Path, dest: Path) -> None:
    dest_resolved = dest.resolve()
    with zipfile.ZipFile(zpath, "r") as zf:
        for member in zf.infolist():
            if member.filename.startswith(("/", "\\")) or ".." in Path(member.filename).parts:
                raise SpawnError("zip entry escapes staging directory (path traversal)")
            out = (dest / member.filename).resolve()
            try:
                out.relative_to(dest_resolved)
            except ValueError:
                raise SpawnError("zip entry escapes staging directory (path traversal)") from None
            out.parent.mkdir(parents=True, exist_ok=True)
            if member.is_dir():
                continue
            with zf.open(member, "r") as src, open(out, "wb") as dst:
                shutil.copyfileobj(src, dst)


def _download_zip(url: str, dest_zip: Path) -> None:
    with httpx.Client(follow_redirects=True, timeout=120.0) as client:
        r = client.get(url)
        r.raise_for_status()
        dest_zip.write_bytes(r.content)


def _resolve_local_spec(path_str: str) -> Path:
    p = Path(path_str).expanduser()
    if not p.exists():
        raise SpawnError(f"local path does not exist: {path_str!r}")
    return p.resolve()


def stage_repository_root(path: str, branch: str | None, temp_base: Path) -> Path:
    """Return the root of a cloned or extracted repository (for build manifests or target repos)."""
    p = urlparse(path)
    if p.scheme in ("http", "https"):
        if path.lower().endswith(".zip"):
            ensure_dir(temp_base)
            zf = temp_base / "repo.zip"
            _download_zip(path, zf)
            out = temp_base / "zip_out"
            ensure_dir(out)
            _extract_zip(zf, out)
            subs = sorted(d for d in out.iterdir() if d.is_dir())
            return subs[0] if len(subs) == 1 else out
        _ensure_git()
        cl = temp_base / "git_out"
        _git_clone(path, branch, cl)
        subs = sorted(d for d in cl.iterdir() if d.is_dir())
        if len(subs) == 1 and not (cl / "spawn").is_dir():
            return subs[0]
        return cl
    local = _resolve_local_spec(path)
    if local.is_file() and local.suffix.lower() == ".zip":
        ensure_dir(temp_base)
        out = temp_base / "local_zip"
        ensure_dir(out)
        _extract_zip(local, out)
        subs = sorted(d for d in out.iterdir() if d.is_dir())
        return subs[0] if len(subs) == 1 else out
    return local


def _find_build_manifest(root: Path) -> Path:
    mf = root / "extensions.yaml"
    if mf.is_file():
        return mf
    subs = sorted(d for d in root.iterdir() if d.is_dir())
    if len(subs) == 1:
        nested = subs[0] / "extensions.yaml"
        if nested.is_file():
            return nested
    raise SpawnError("extensions.yaml not found in build source")


def _materialize_files(target_root: Path, extension: str, config: ExtensionConfig) -> None:
    ext_root = _spawn_extend(target_root, extension)
    files_src = ext_root / "files"
    for rel_path, ent in config.files.items():
        dest = safe_path(target_root, rel_path.replace("\\", "/"))
        src = files_src.joinpath(*Path(rel_path).parts)
        if ent.mode == FileMode.static:
            if not src.is_file():
                continue
            if dest.exists() and dest.is_file():
                warnings.warn(
                    f"Replacing existing file from extension (static): {rel_path}",
                    SpawnWarning,
                )
            ensure_dir(dest.parent)
            shutil.copy2(src, dest)
        else:
            if not src.is_file():
                continue
            if not dest.exists():
                ensure_dir(dest.parent)
                shutil.copy2(src, dest)


def _copy_extsrc_tree(extsrc_dir: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(extsrc_dir, dest, dirs_exist_ok=False)


def _stage_from_path_string(
    target_root: Path,
    path: str,
    branch: str | None,
    temp_base: Path,
) -> tuple[Path, SourceYaml.SourceInfo]:
    del target_root
    p = urlparse(path)
    if p.scheme in ("http", "https"):
        if path.lower().endswith(".zip"):
            ensure_dir(temp_base)
            zf = temp_base / "src.zip"
            _download_zip(path, zf)
            extract_to = temp_base / "zip_out"
            ensure_dir(extract_to)
            _extract_zip(zf, extract_to)
            extsrc_root = extract_to
            for child in sorted(extract_to.iterdir(), key=lambda x: x.name):
                if child.is_dir() and (child / "extsrc").is_dir():
                    extsrc_root = child
                    break
            extdir = _find_extsrc(extsrc_root if (extsrc_root / "extsrc").is_dir() else extsrc_root)
            return extdir, SourceYaml.SourceInfo(type="zip", path=path, branch=None, resolved=None)
        _ensure_git()
        clone_dir = temp_base / "git"
        _git_clone(path, branch, clone_dir)
        root = clone_dir
        if (root / "extsrc" / "config.yaml").is_file():
            pass
        else:
            subdirs = [d for d in root.iterdir() if d.is_dir()]
            if subdirs and (subdirs[0] / "extsrc" / "config.yaml").is_file():
                root = subdirs[0]
        extdir = _find_extsrc(root)
        return extdir, SourceYaml.SourceInfo(type="git", path=path, branch=branch, resolved=None)
    local = _resolve_local_spec(path)
    if local.is_file() and local.suffix.lower() == ".zip":
        ensure_dir(temp_base)
        extract_to = temp_base / "local_zip"
        ensure_dir(extract_to)
        _extract_zip(local, extract_to)
        extdir = _find_extsrc(extract_to)
        return extdir, SourceYaml.SourceInfo(type="zip", path=str(local), branch=None, resolved=None)
    extdir = _find_extsrc(local)
    return extdir, SourceYaml.SourceInfo(type="local", path=str(local), branch=branch, resolved=None)


@dataclass
class StagedExtension:
    extsrc_dir: Path
    source_info: SourceYaml.SourceInfo
    config: ExtensionConfig
    temp_base: Path

    def cleanup(self) -> None:
        if self.temp_base.exists():
            shutil.rmtree(self.temp_base, ignore_errors=True)


def _stage_extension(
    target_root: Path | None,
    path: str,
    branch: str | None,
    *,
    require_init: bool,
) -> StagedExtension:
    if require_init:
        if target_root is None:
            raise SpawnError("target_root is required when require_init is True")
        _require_init(target_root)
    op = str(uuid.uuid4())
    if target_root is not None:
        parent = target_root / "spawn" / ".metadata" / "temp"
    else:
        parent = Path(tempfile.gettempdir()) / "spawn-stage"
    temp_base = parent / op
    ensure_dir(temp_base.parent)
    ll.prune_metadata_temp(
        temp_base.parent,
        max_age_seconds=ll.METADATA_TEMP_MAX_AGE_SECONDS,
        reserved=op,
    )
    try:
        anchor = target_root if target_root is not None else Path.cwd()
        extsrc_dir, source_info = _stage_from_path_string(anchor, path, branch, temp_base)
        raw = load_yaml(extsrc_dir / "config.yaml")
        if not raw:
            raise SpawnError("extsrc/config.yaml missing or empty")
        cfg = ExtensionConfig.model_validate(raw)
        return StagedExtension(extsrc_dir=extsrc_dir, source_info=source_info, config=cfg, temp_base=temp_base)
    except BaseException:
        if temp_base.exists():
            shutil.rmtree(temp_base, ignore_errors=True)
        raise


def download_extension(target_root: Path, path: str, branch: str | None = None) -> str:
    """Stage, validate, copy extension into spawn/.extend/{name}, write source.yaml. Returns extension name."""
    staged = _stage_extension(target_root, path, branch, require_init=True)
    try:
        candidate_cfg = staged.config
        ext_name = candidate_cfg.name or "extension"
        _check_install_version_and_source(target_root, ext_name, candidate_cfg, staged.source_info)
        _check_path_conflicts(target_root, candidate_cfg, ext_name)
        _validate_render_identity_for_new_extension(target_root, ext_name, staged.extsrc_dir)
        scripts.run_before_install_scripts(target_root, ext_name, ext_layout=staged.extsrc_dir)
        dest = _spawn_extend(target_root, ext_name)
        ensure_dir(dest.parent)
        _copy_extsrc_tree(staged.extsrc_dir, dest)
        _write_source_yaml(target_root, ext_name, staged.source_info, candidate_cfg.version)
        _materialize_files(target_root, ext_name, candidate_cfg)
        return ext_name
    finally:
        staged.cleanup()


def install_extension(target_root: Path, path: str, branch: str | None = None) -> None:
    from spawn_cli.core import high_level as hl

    hl.install_extension(target_root, path, branch)


def install_build(target_root: Path, path: str, branch: str | None = None) -> None:
    for ent in list_build_extensions(path, branch):
        p_ent = ent.get("path")
        if not p_ent:
            continue
        br = ent.get("branch")
        install_extension(target_root, str(p_ent), br if br is not None else branch)


def list_build_extensions(path: str, branch: str | None = None) -> list[dict]:
    root = Path(path).expanduser().resolve()
    if root.is_dir() and (root / "extensions.yaml").is_file():
        raw = load_yaml(root / "extensions.yaml")
        meta = ExtensionsMeta.model_validate(raw)
        return [e.model_dump() for e in meta.extensions]

    td = Path(tempfile.mkdtemp(prefix="spawn-build-list-"))
    try:
        work = td / "stage"
        repo_root = stage_repository_root(str(path), branch, work)
        mf = _find_build_manifest(repo_root)
        raw = load_yaml(mf)
        meta = ExtensionsMeta.model_validate(raw)
        return [e.model_dump() for e in meta.extensions]
    finally:
        shutil.rmtree(td, ignore_errors=True)


__all__ = [
    "StagedExtension",
    "compare_version_strings",
    "download_extension",
    "install_build",
    "install_extension",
    "list_build_extensions",
    "stage_repository_root",
    "_check_install_version_and_source",
    "_copy_extsrc_tree",
    "_find_build_manifest",
    "_load_stored_source",
    "_materialize_files",
    "_spawn_extend",
    "_source_info_key",
    "_stage_extension",
    "_validate_render_identity_for_new_extension",
    "_write_source_yaml",
]
