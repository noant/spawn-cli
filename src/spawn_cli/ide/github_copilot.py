"""GitHub Copilot IDE adapter: .github/skills, .vscode/mcp.json (servers + inputs), dual entry points."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

from spawn_cli.ide.registry import (
    DetectResult,
    IdeAdapter,
    IdeCapabilities,
    register,
    normalize_skill_name,
    render_skill_md,
    rewrite_managed_block,
)
from spawn_cli.models.mcp import McpServer, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


def _env_input_id(server_name: str, var_name: str) -> str:
    return f"{server_name}-{var_name.lower().replace('_', '-')}"


def _build_vscode_mcp_entry(server: McpServer) -> tuple[dict, list[dict]]:
    transport = server.transport
    entry: dict = {}
    inputs: list[dict] = []

    if transport.type == "stdio":
        entry["type"] = "stdio"
        entry["command"] = transport.command
        entry["args"] = list(transport.args)
    else:
        entry["type"] = transport.type
        entry["url"] = transport.url

    if server.env:
        env_dict: dict[str, str] = {}
        for var_name, var in server.env.items():
            if var.secret:
                input_id = _env_input_id(server.name, var_name)
                env_dict[var_name] = f"${{input:{input_id}}}"
                inputs.append(
                    {
                        "id": input_id,
                        "type": "promptString",
                        "description": var_name,
                        "password": True,
                    }
                )
            else:
                env_dict[var_name] = var.value or f"${{{var_name}}}"
        entry["env"] = env_dict

    return entry, inputs


def _input_belongs_to_server(inp_id: str, server_name: str) -> bool:
    prefix = f"{server_name}-"
    return inp_id.startswith(prefix)


class GitHubCopilotAdapter(IdeAdapter):
    key = "github-copilot"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".github").exists() or (target_root / ".vscode").exists()
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="unsupported",
                entry_point="copilot-instructions",
            ),
        )

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".github" / "skills" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_path = skill_dir / "SKILL.md"
            if skill_path.exists():
                warnings.warn(f"Overwriting existing rendered skill: {skill_path}")
            skill_path.write_text(render_skill_md(skill), encoding="utf-8")
            rel = skill_path.relative_to(target_root).as_posix()
            results.append({"skill": skill.name, "path": rel})
        return results

    def remove_skills(self, target_root: Path, rendered_paths: list[dict]) -> None:
        for entry in rendered_paths:
            p = target_root / entry["path"]
            if p.exists():
                p.unlink()
            if p.parent.exists() and not any(p.parent.iterdir()):
                p.parent.rmdir()

    def add_mcp(self, target_root: Path, normalized_mcp: NormalizedMcp) -> list[str]:
        mcp_path = target_root / ".vscode" / "mcp.json"
        mcp_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(mcp_path.read_text(encoding="utf-8")) if mcp_path.exists() else {}
        data.setdefault("servers", {})
        data.setdefault("inputs", [])
        if not isinstance(data["inputs"], list):
            data["inputs"] = []
        rendered_names = []
        existing_ids = {inp["id"] for inp in data["inputs"] if isinstance(inp, dict) and "id" in inp}
        for server in normalized_mcp.servers:
            entry, new_inputs = _build_vscode_mcp_entry(server)
            data["servers"][server.name] = entry
            for inp in new_inputs:
                if inp["id"] not in existing_ids:
                    data["inputs"].append(inp)
                    existing_ids.add(inp["id"])
            rendered_names.append(server.name)
        mcp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return rendered_names

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        mcp_path = target_root / ".vscode" / "mcp.json"
        if not mcp_path.exists():
            return
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
        for name in rendered_mcp_names:
            data.get("servers", {}).pop(name, None)
        removed = set(rendered_mcp_names)
        inputs_list = data.get("inputs", [])
        if isinstance(inputs_list, list):
            data["inputs"] = [
                inp
                for inp in inputs_list
                if not isinstance(inp, dict)
                or "id" not in inp
                or not any(_input_belongs_to_server(str(inp["id"]), n) for n in removed)
            ]
        mcp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        del target_root, globs
        warnings.warn(
            "github-copilot: agent ignore is unsupported; "
            "GitHub Copilot content exclusion does not apply to IDE Agent mode"
        )

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        del target_root, globs
        warnings.warn("github-copilot: agent ignore is unsupported")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep1 = target_root / ".github" / "copilot-instructions.md"
        ep2 = target_root / "AGENTS.md"
        rewrite_managed_block(ep1, prompt)
        rewrite_managed_block(ep2, prompt)
        return ep1.relative_to(target_root).as_posix()


register(GitHubCopilotAdapter())

__all__ = ["GitHubCopilotAdapter"]
