# 29: Mimo Code IDE adapter

## Source seed
- Path: spec/seeds/6-mimo-code-adapter.md

## Status
- [V] Research [glm-5.3 + kimi-k3]
- [V] User research review
- [V] Spec drafting [glm-5.3-flash]
- [V] Spec self-review [glm-5.3 + deepseek-v4-pro]
- [ ] Spec review
- [V] Code implementation [glm-5.3-flash]
- [V] Code self-review [glm-5.3-flash]
- [ ] Code review / debugging
- [V] Design document update [glm-5.3-flash]

## Goal
Implement a full Mimo Code IDE adapter (`src/spawn_cli/ide/mimo_code.py`) registered as `mimo-code`, replacing the absent stub, mirroring the OpenCode adapter.

## Motivation
New feature: spawn must manage skills, MCP servers, agent ignore rules, and the AGENTS.md entry point for Xiaomi's MiMo Code agent (OpenCode fork), as it already does for OpenCode, Codex, and other IDEs.

## Invasiveness level
medium-invasive — new adapter module plus edits in core key list, IDE package wiring, vacancy pruner, and tests.

## Review models
- Research review: single agent: glm-5.3-flash
- Spec review: cross-review: glm-5.3, kimi-k3.1-pro
- Code review: single agent: glm-5.3-flash

## Run mode
auto — fully LLM-run, no user participation; user confirmations (Steps 4, 7) skipped, checkboxes left unchecked.

## Research summary
Two cross-checked research lines (files: `research-a-glm.md`, `research-b-kimi.md`, review by glm-5.3-flash passed with minor fixes).
- MiMo Code is Xiaomi's OpenCode fork; conventions nearly identical to OpenCode.
- Detect markers: `.mimocode/` dir, or `.mimocode/mimocode.json` / `mimocode.jsonc` (project config). `AGENTS.md` alone is not a valid marker (shared by many agents).
- Skills: `.mimocode/skills/<name>/SKILL.md`; name from YAML frontmatter (name required), no strict regex; standard `normalize_skill_name` suffices; keep dirname == frontmatter name.
- MCP: root key `mcp` in the canonical config; entries `{"type": "local"|"remote", ...}` — same shape as `opencode.json` (`opencode.py:_build_mcp_entry` reusable pattern).
- Agent ignore: no dedicated ignore file; use `permission.read` / `permission.edit` glob -> `"deny"` dict entries (same as opencode.py).
- Entry point: root `AGENTS.md` managed block via `rewrite_managed_block`.
- Canonical config rule (spawn/rules/05): canonical file is `.mimocode/mimocode.json`; warn (SpawnWarning) when only `.jsonc` exists; raise SpawnError on unparseable canonical file.
- Registration: `mimo-code` is absent from `CANONICAL_IDE_KEYS` (src/spawn_cli/core/low_level.py:28-37) and nowhere in src/ or tests/ — must be added; `register()` raises SpawnError otherwise (registry.py:110-115).
- Vacancy cleanup: new `finalize_mimo_code_repo` in `_vacancy.py` mirroring `finalize_opencode_repo` (rule spawn/rules/01).
- Skill name constraints rule 04: not required (MiMo reads name from frontmatter).
- Closest template: `src/spawn_cli/ide/opencode.py`; tests mirror `tests/ide/test_opencode.py`.

## Design overview
- Affected modules: `spawn_cli.core.low_level`, `spawn_cli.ide` (registry wiring, new adapter, vacancy), `tests.ide`.
- Files & symbols:
  - `src/spawn_cli/core/low_level.py` — `CANONICAL_IDE_KEYS` (append `"mimo-code"`).
  - `src/spawn_cli/ide/mimo_code.py` — new `MimoCodeAdapter(IdeAdapter)`, `_CONFIG`, `_load_config`, `_save_config`, `_build_mcp_entry`, `register(MimoCodeAdapter())`.
  - `src/spawn_cli/ide/__init__.py` — module import, `MimoCodeAdapter` re-export, `__all__`.
  - `src/spawn_cli/ide/registry.py` — `ALIASES` add `"mimo": "mimo-code"`.
  - `src/spawn_cli/ide/_vacancy.py` — `finalize_mimo_code_repo`, `__all__`.
  - `tests/ide/test_mimo_code.py` — new test module mirroring `tests/ide/test_opencode.py`.
- Data flow changes: none outside the adapter contract; spawn CLI writes `.mimocode/mimocode.json` (mcp, permission keys), `.mimocode/skills/<name>/SKILL.md`, and the AGENTS.md spawn block.
- Integration points: `IdeAdapter` registry (`detect_supported_ides` picks up the new key automatically), `mcp_stdio_argv` proxy, `_vacancy` pruner, `ll.get_agent_ignore_list`.

## Before -> After
### Before
- No `mimo-code` key, no Mimo adapter; MiMo Code users cannot use spawn skills/MCP/ignore/entry-point management.
### After
- `mimo-code` is a first-class canonical IDE key with a full `MimoCodeAdapter` (skills native, MCP project, agent-ignore project, entry point agents-md), vacancy cleanup, alias `mimo`, and full peer-parity tests.

## Details
- Capabilities (DetectResult): skills="native", mcp="project", agent_ignore="project", entry_point="agents-md" (identical to opencode).
- detect: `used_in_repo = (target_root / ".mimocode").exists()` — covers the config dir including skills/agents/commands subdirs and the config file inside it; keep it to the single dir check (config files all live under `.mimocode/`).
- Canonical config: `_CONFIG = ".mimocode/mimocode.json"`; `_load_config` warns `SpawnWarning` when the canonical file is absent but `.mimocode/mimocode.jsonc` exists; raises `SpawnError` on invalid JSON.
- Skill name: use `normalize_skill_name` (no extra sanitization; MiMo reads frontmatter name, rule 04 not needed); render with `render_skill_md(skill.model_copy(update={"name": name}))`; overwrite warning via SpawnWarning.
- MCP entries: copy `_build_mcp_entry` semantics from opencode.py (local/remote, spawn stdio proxy via `mcp_stdio_argv`, `{env:K}` secret placeholders, `enabled: true`).
- Agent ignore: mirror opencode `add_agent_ignore` / `remove_agent_ignore` on `permission.read` / `permission.edit`; `clear_spawn_agent_ignore` reads recorded globs via `ll.get_agent_ignore_list(target_root, self.key)`.
- Entry point: root `AGENTS.md`, `rewrite_managed_block`.
- Warnings/errors: `SpawnWarning`/`SpawnError` from `spawn_cli.errors` (rule 03).
- Vacancy (rule 01): `finalize_mimo_code_repo` mirrors `finalize_opencode_repo` (known spawn keys: `mcp`, `permission`; prune `.mimocode/skills` and empty `.mimocode`).
- Test parity: `tests/ide/test_registry.py` auto-covers the new key; add `mimo` alias and `mimo-code` get-assertions there.

## Execution Scheme
Suggested coordinator model: glm-5.3-flash
> Each step id is the subtask filename (e.g. `1-registration`).
> Each step is executed by a dedicated `A5-coder` subagent (see Step 5).
- Phase 1 (sequential): step 1-registration -> step 2-adapter-module -> step 3-tests
- Phase 2 (sequential): step review — inspect all changes, fix inconsistencies
