linked task: none

## Idea (informal)

Full IDE adapter for **OpenCode CLI** (`src/spawn_cli/ide/opencode.py`), replacing `StubAdapter`.

### Research plan (features to look for)

- Project detection markers: config dir/file (`.opencode/`, `opencode.json`), skills directory layout.
- Native skill/agent support: does OpenCode load `SKILL.md` files; where are skills/commands placed; naming constraints.
- MCP support: project-scope config file and format (JSON/TOML), stdio vs http entries, proxy support.
- Agent ignore: supported ignore file, syntax, managed-block strategy.
- Entry point file: AGENTS.md equivalent or native rules file; managed block rewriting.
- Precedents: `codex.py` (AGENTS.md + toml MCP), `gemini_cli.py`, `cursor.py`.
- Must cover: `detect`, `add_skills`, `remove_skills`, MCP add/remove, agent ignore, entry point; registration at import; extend `CANONICAL_IDE_KEYS` in `spawn_cli.core.low_level` in design-approved order; tests mirroring peer adapters.

### Sub-agent model assignments

- Research agent: GLM-5.3 and Kimi-k3 (two lines, cross-checked).
- Spec synthesis (drafting): GLM-5.3-flash.
- Spec review: GLM-5.3.
- Implementation: GLM-5.3-flash.

When promoting this seed, run **spectask-create**.
