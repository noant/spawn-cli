linked task: none

## Idea (informal)

Full IDE adapter for **Hermes** (`src/spawn_cli/ide/hermes.py`), replacing `StubAdapter`.

### Research plan (features to look for)

- Project detection markers: config dir/file, distinct artifacts in the repo.
- Skill/agent support: does Hermes load `SKILL.md`; skill directory path and naming rules.
- MCP support: project-scope config location and format; stdio/http transport entries; proxy support.
- Agent ignore: supported ignore file, syntax, managed-block strategy.
- Entry point file: rules/instructions file path and format; managed block rewriting.
- Precedents: `codex.py`, `claude_code.py`, `windsurf.py`.
- Must cover: `detect`, `add_skills`, `remove_skills`, MCP add/remove, agent ignore, entry point; registration at import; `CANONICAL_IDE_KEYS` ordering; tests mirroring peer adapters.

### Sub-agent model assignments

- Research agent: GLM-5.3 and Kimi-k3 (two lines, cross-checked).
- Spec synthesis (drafting): GLM-5.3-flash.
- Spec review: GLM-5.3 + Kimi-k3.1-pro.
- Implementation: GLM-5.3-flash.

When promoting this seed, run **spectask-create**.
