# 30: Full IDE adapter for Hermes

## Source seed
- Path: spec/seeds/7-hermes-adapter.md

## Status
- [V] Research [glm-5.3 + deepseek-v4-pro]
- [V] User research review
- [V] Spec drafting [glm-5.3-flash]
- [V] Spec self-review [glm-5.3 + deepseek-v4-pro]
- [ ] Spec review
- [V] Code implementation [glm-5.3-flash]
- [V] Code self-review [glm-5.3-flash]
- [ ] Code review / debugging
- [V] Design document update [glm-5.3-flash]

## Goal
Add a full project-scoped IDE adapter for Hermes Agent (Nous Research) under key "hermes", replacing the unregistered stub approach with a concrete `HermesAdapter`.

## Motivation
New feature: spawn currently has no adapter for Hermes Agent; `get("hermes")` raises "Unknown IDE". Users of Hermes cannot install spawn skills or get an entry-point block.

## Invasiveness level
medium-invasive — new adapter file + registration (low_level, __init__, _vacancy) + tests; peer adapters untouched.

## Review models
- Research review: single agent: glm-5.3-flash
- Spec review: cross-review: glm-5.3, kimi-k3.1-pro
- Code review: single agent: glm-5.3-flash

## Run mode
auto — user confirmations (Steps 4, 7) skipped; checkboxes left unchecked.

## Research summary
Two cross lines (glm-5.3, deepseek-v4-pro) + review (glm-5.3-flash). Reviewer verdict: line B (deepseek-v4-pro) wins on all 4 disagreements.
- Repo: `CANONICAL_IDE_KEYS` (src/spawn_cli/core/low_level.py:28) = ("cursor","codex","claude-code","windsurf","github-copilot","gemini-cli","cline","opencode"); "hermes" absent; StubAdapter never registered (only tests use it). `register()` validates key membership (registry.py:110). Append-only ordering convention.
- Hermes Agent (Nous Research, hermes-agent.nousresearch.com) facts: MCP config ONLY global (`~/.hermes/config.yaml`, key `mcp_servers`) — no project-scope MCP; no agent-ignore file; project skills supported at `<root>/.hermes/skills/<name>/SKILL.md` (after `hermes skills trust`); project context priority: `.hermes.md` > AGENTS.override.md > AGENTS.md > CLAUDE.md; `SOUL.md` is global-only.
- Design (per reviewer): skills=native (`.hermes/skills/<name>/SKILL.md`, mirror codex/cline), mcp=unsupported (SpawnWarning, mirror cline), agent_ignore=unsupported (SpawnWarning), entry_point="hermes-md" (root `.hermes.md` via `rewrite_managed_block`), detect = `.hermes` dir or `.hermes.md`/`HERMES.md` file, finalize via `finalize_standard_dotdir_skills_and_mcp(root, ".hermes", allow_delete_entire=True)`.
- No ALIASES entry needed; skip hermes param in test_mcp_stdio_proxy_parity.py (mcp unsupported).

## Design overview
- Affected modules: `spawn_cli.core.low_level`, `spawn_cli.ide` (new `hermes` module, `__init__` registration), `spawn_cli.ide._vacancy`, `tests.ide`.
- Files & symbols:
  - `src/spawn_cli/core/low_level.py` — `CANONICAL_IDE_KEYS`
  - `src/spawn_cli/ide/hermes.py` — new `HermesAdapter` (detect, add_skills, remove_skills, add_mcp, remove_mcp, add_agent_ignore, remove_agent_ignore, rewrite_entry_point, finalize_repo_after_ide_removed)
  - `src/spawn_cli/ide/__init__.py` — import + export
  - `src/spawn_cli/ide/_vacancy.py` — new `finalize_hermes_repo`
  - `tests/ide/test_hermes.py` — new
  - `tests/ide/test_registry.py` — extend `test_get_known_adapter`
  - `tests/ide/test_vacancy.py` — add hermes finalize case
- Data flow changes: `spawn install/refresh --ide hermes` writes `.hermes/skills/<name>/SKILL.md` and a spawn-managed block in root `.hermes.md`; MCP/ignore ops warn unsupported.
- Integration points: registry (`register` at import), `CANONICAL_IDE_KEYS` ordering (append last), vacancy pruning on IDE removal.

## Before → After
### Before
- `"hermes"` unknown: `get("hermes")` raises `SpawnError("Unknown IDE: 'hermes'")`; no way to target Hermes.
### After
- `get("hermes")` returns `HermesAdapter`; `detect_supported_ides()` includes hermes; install/refresh write project skills + `.hermes.md` entry block; unsupported ops emit `SpawnWarning`.

## Details
- Style: use `warnings.warn(..., SpawnWarning)` like `cline.py:76-85` for unsupported ops; plain `warnings.warn` for skill overwrite (cline.py:57).
- Entry point capability string: new value `"hermes-md"` (native highest-priority context file), NOT "agents-md" — spawn block in AGENTS.md may be shadowed by `.hermes.md`.
- Project skills require `hermes skills trust` before Hermes loads them — document in module docstring as onboarding caveat (not a blocker).
- `.agents/skills` intentionally NOT used (owned by Codex adapter); use `.hermes/skills` to avoid collision.
- Do not touch peer adapters; do not modify `test_mcp_stdio_proxy_parity.py` (hermes has no MCP support).

## Execution Scheme
Suggested coordinator model: glm-5.3-flash
> Each step id is the subtask filename. Each step is executed by a dedicated `A5-coder` subagent (see Step 5).
- Phase 1 (sequential): step 1-registry-keys → step 2-hermes-adapter → step 3-tests
