linked task: none

## Idea (informal)

Full IDE adapter for **JetBrains Junie** (`src/spawn_cli/ide/junie.py`), replacing `StubAdapter`.

### Research plan (features to look for)

- Project detection markers: `.junie/` directory or JetBrains-specific config artifacts.
- Skill/agent support: guidelines/instructions format (Junie guidelines file), placement, syntax; native `SKILL.md` support if any.
- MCP support: does Junie consume MCP servers; project-scope config file and format; proxy support.
- Agent ignore: ignore/exclude mechanism, syntax, managed-block strategy.
- Entry point file: Junie guidelines vs AGENTS.md; managed block rewriting.
- Precedents: `codex.py` (AGENTS.md), `cursor.py` (IDE conventions).
- Must cover: `detect`, `add_skills`, `remove_skills`, MCP add/remove, agent ignore, entry point; registration at import; `CANONICAL_IDE_KEYS` ordering; tests mirroring peer adapters.

### Sub-agent model assignments

- Research agent: GLM-5.3 and Kimi-k3 (two lines, cross-checked).
- Spec synthesis (drafting): GLM-5.3-flash.
- Spec review: GLM-5.3.
- Implementation: GLM-5.3-flash.

When promoting this seed, run **spectask-create**.
