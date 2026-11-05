linked task: none

## Idea (informal)

Full IDE adapter for **Cline** (`src/spawn_cli/ide/cline.py`), replacing `StubAdapter`.

Note: **GitHub Copilot for VS Code already has a full adapter** (`src/spawn_cli/ide/github_copilot.py`) — no seed needed for it.

### Research plan (features to look for)

- Project detection markers: `.clinerules/`, cline settings files in the repo/workspace.
- Skill/agent support: custom instructions / workflows / modes placement (`~/.cline` vs project scope); naming rules.
- MCP support: `cline_mcp_settings.json` (project-scope), transport entries (stdio/http), proxy support.
- Agent ignore: `.clineignore` file — exact path, syntax (gitignore-style?), managed-block strategy.
- Entry point file: `.clinerules` files vs AGENTS.md; managed block rewriting.
- Precedents: `github_copilot.py` (VS Code family), `cursor.py`, `windsurf.py`.
- Must cover: `detect`, `add_skills`, `remove_skills`, MCP add/remove, agent ignore, entry point; registration at import; `CANONICAL_IDE_KEYS` ordering; tests mirroring peer adapters.

### Sub-agent model assignments

- Research agent: GLM-5.3 and Kimi-k3 (two lines, cross-checked).
- Spec synthesis (drafting): GLM-5.3-flash.
- Spec review: GLM-5.3.
- Implementation: GLM-5.3-flash.

When promoting this seed, run **spectask-create**.
