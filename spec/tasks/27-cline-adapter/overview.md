# 27: Cline IDE adapter

## Source seed
- Path: spec/seeds/9-cline-adapter.md

## Status
- [V] Research [glm-5.3 + kimi-k3.1-pro]
- [V] User research review
- [V] Spec drafting [glm-5.3-flash]
- [V] Spec self-review [glm-5.3 + kimi-k3.1-pro]
- [ ] Spec review
- [ ] Code implementation [model]
- [ ] Code self-review [model]
- [ ] Code review / debugging
- [ ] Design document update [model]

## Goal
Implement a full Cline IDE adapter (`src/spawn_cli/ide/cline.py`) and register it under canonical IDE key `cline`, replacing the conceptual `StubAdapter` usage.

## Motivation
new feature — add Cline (VS Code extension + CLI) as a supported IDE so Spawn can install navigation, skills, agent ignore, and entry point metadata into Cline-managed repositories.

## Invasiveness level
minimally-invasive — one new adapter file, registration points, vacancy finalizer, tests; no changes to adapter contracts or orchestration.

## Review models
- Research review: single agent: glm-5.3
- Spec review: cross-review: glm-5.3, kimi-k3.1-pro
- Code review: cross-review: glm-5.3, kimi-k3.1-pro

## Run mode
interactive

## Research summary
Cross-researched by glm-5.3 and kimi-k3.1-pro (merged; research review by glm-5.3: ALL OK).

### External Cline facts (docs.cline.bot + cline/cline sources)
- Detection markers (project root): `.cline/` dir (modern layout: rules/, workflows/, skills/, hooks/), `.clinerules/` dir or single `.clinerules` legacy file, `.clineignore`. Do NOT use AGENTS.md as a marker (cross-tool).
- Skills: `.cline/skills/<name>/SKILL.md`; frontmatter `name` must exactly match the directory name (lowercase kebab-case recommended); `description` max 1024 chars. Sources: docs.cline.bot/customization/skills.
- Rules: modern `.cline/rules/`, legacy `.clinerules/`; workflows `.cline/workflows/` — out of IdeAdapter scope.
- MCP: NO project-scope MCP settings exist. Cline CLI uses global `~/.cline/data/settings/cline_mcp_settings.json` (override via `CLINE_MCP_SETTINGS_PATH`); the VS Code extension stores settings outside the repo. `.cline/mcp.json` / repo `cline_mcp_settings.json` are not supported paths — Cline will not load them. Decision: capability `mcp="unsupported"`, mirroring Windsurf: `add_mcp` warns and returns `[]`; `remove_mcp` is a no-op. Do not invent repo config files. Sources: docs.cline.bot/mcp/mcp-overview, cline/cline paths.ts.
- Agent ignore: `.clineignore` at project root, gitignore-style (globs, `!` negations, comments; also nonstandard `!include`). Officially deprecated-soon (moving to hooks) but still functional; it is the only project-scope mechanism. Spawn `# spawn:*` markers are plain comments — managed-block helpers apply unchanged.
- Entry point: Cline reads project-root `AGENTS.md` automatically (and global `~/.agents/AGENTS.md`). Use `rewrite_managed_block` on `AGENTS.md`; capability `entry_point="agents-md"`.

### Codebase findings (verified by reviewer)
- Contract: `src/spawn_cli/ide/registry.py` — IdeAdapter ABC (detect, add_skills -> list[{"skill","path"}], remove_skills, add_mcp -> list[str], remove_mcp, add/remove_agent_ignore, rewrite_entry_point -> rel posix path; optional rewrite_core_agent_ignore / rewrite_extension_agent_ignore / clear_spawn_agent_ignore / finalize_repo_after_ide_removed). DetectResult(used_in_repo, capabilities); IdeCapabilities(skills, mcp, agent_ignore, entry_point) values native|project|entry-only|external|unsupported (plus special entry values like "agents-md").
- Registration points: `CANONICAL_IDE_KEYS` tuple in `src/spawn_cli/core/low_level.py:28` (append `"cline"` after `"gemini-cli"`; ordering defines detection/output order); `src/spawn_cli/ide/__init__.py` (import module for side-effect registration + export ClineAdapter in `__all__`); `src/spawn_cli/ide/_vacancy.py` (new `finalize_cline_repo`).
- `StubAdapter` (`_stub.py`) is a generic class used by tests; no registered stub for "cline" exists — "replacing StubAdapter" is conceptual; `_stub.py` stays.
- Helpers available in `_helpers.py`: `normalize_skill_name`, `render_skill_md` (line 43), `rewrite_managed_block` (73), `rewrite_ignore_block` (108) / `remove_ignore_block` (270), split-flow `rewrite_core_agent_ignore_region` (255) / `rewrite_extension_agent_ignore_region` (260) / `clear_split_agent_ignore_file` (265); `finalize_standard_dotdir_skills_and_mcp` in `_vacancy.py` fits `.cline/`.
- Orchestration: for `agent_ignore="native"`, high_level calls the split core/ext methods (high_level.py:98,109); `remove_ide` runs remove_skills + `clear_spawn_agent_ignore` (645) then `finalize_repo_after_ide_removed` (640-646).
- Known pitfall (verified): `render_skill_md` writes frontmatter `name: {skill.name}` (original name, _helpers.py:49) while the skill directory uses `normalize_skill_name(skill.name)`. Cline requires `name == dirname`, so the Cline adapter must render with a normalized-name copy (`skill.model_copy(update={"name": name})`), and tests must assert frontmatter name equals directory name.
- Rules implications: `spawn/rules/01-vacancy-cleanup-subtrees.md` — `finalize_cline_repo` must know `.cline` dotdir and `.clineignore`; deletion only when empty/vacant, user content preserved. Rule 02 (namespaced profiles) not applicable — dedicated ignore file.
- Tests: `tests/ide/test_cline.py` mirroring peers (tmp_path, adapter fixture): detect per marker + capabilities, skills add/remove (incl. frontmatter name == dirname, overwrite warning, extra-file retention), MCP unsupported warning + no files written, ignore add/remove/idempotency/legacy-block migration/clear, entry point create/replace, finalize vacancy mirroring the remove_ide flow, updates to `tests/ide/test_registry.py`.

### Research disagreements
None material: both lines independently concluded mcp="unsupported" (windsurf precedent), skills in `.cline/skills/`, native `.clineignore`, AGENTS.md entry point. Reviewer confirmed all load-bearing claims with file:line or URLs.

### Spec self-review outcome (cross glm-5.3 + kimi-k3.1-pro)
Defects found and fixed in this spec: missing `_vacancy.py` import of `clear_split_agent_ignore_file`; finalizer now strips split core/ext blocks (not only legacy); finalize tests must mirror the remove_ide flow (remove_skills + clear_spawn_agent_ignore before finalize); concrete Before/After added for the `test_registry.py` import; extra-file retention, ignore idempotency/migration, and entry-point replace test coverage added; finalizer tests given explicit Before/After pairs.

## Design overview
- Affected modules: `spawn_cli.ide` (new adapter), `spawn_cli.core.low_level` (canonical keys), `spawn_cli.ide._vacancy` (finalize), tests.
- Files & symbols:
  - `src/spawn_cli/ide/cline.py` — new `ClineAdapter(IdeAdapter)`, `key="cline"`, `register(ClineAdapter())`.
  - `src/spawn_cli/core/low_level.py` — `CANONICAL_IDE_KEYS` += `"cline"`.
  - `src/spawn_cli/ide/__init__.py` — import `cline` module; export `ClineAdapter`.
  - `src/spawn_cli/ide/_vacancy.py` — new `finalize_cline_repo(target_root)` + import of `clear_split_agent_ignore_file`.
  - `tests/ide/test_cline.py` — new; `tests/ide/test_registry.py` — extend for `cline`.
- Data flow changes: none; adapter follows existing adapter-utility-metadata contract.
- Integration points: registry `get("cline")`, high_level refresh flows (skills, MCP unsupported warning path, split agent ignore), remove_ide -> finalize_cline_repo.

## Before -> After
### Before
- `cline` is absent from `CANONICAL_IDE_KEYS` and the adapter registry; Cline-managed repos cannot be onboarded (`spawn ide add cline` errors on unknown key).
### After
- `spawn ide add cline` renders skills into `.cline/skills/<name>/SKILL.md` (frontmatter name == dirname), maintains managed blocks in `.clineignore`, writes the managed block into `AGENTS.md`, warns on MCP (unsupported, matching Windsurf), and `spawn ide remove cline` cleans up vacant `.cline/` and `.clineignore` without touching user content.

## Details
- Capabilities: skills=native, mcp=unsupported, agent_ignore=native, entry_point=agents-md.
- Skill rendering: reuse `render_skill_md`, but pass `skill.model_copy(update={"name": normalize_skill_name(skill.name)})` so Cline's name==dirname requirement holds; retain "warn on overwrite" behavior from peers.
- Agent ignore: delegate to split helpers (`rewrite_core_agent_ignore_region`, `rewrite_extension_agent_ignore_region`, `clear_split_agent_ignore_file`) with `.clineignore`; `add_agent_ignore`/`remove_agent_ignore` use `rewrite_ignore_block`/`remove_ignore_block` (cursor-style dedicated-file pattern).
- Entry point: `rewrite_managed_block(target_root / "AGENTS.md", prompt)`; return `"AGENTS.md"`.
- MCP: `add_mcp` emits a `warnings.warn` (windsurf wording pattern) and returns `[]`; `remove_mcp` no-op; `spawn_stdio_proxy` parity not applicable (nothing written).
- Finalize: `finalize_cline_repo` = `finalize_standard_dotdir_skills_and_mcp` for `.cline` (allow_delete_entire), then `clear_split_agent_ignore_file` on `.clineignore` and unlink only when no user content remains; never touch `.clinerules` or `AGENTS.md`.

## Execution Scheme
Suggested coordinator model: glm-5.3-flash
> Each step id is the subtask filename.
> Each step is executed by a dedicated `A5-coder` subagent (see Step 5).
- Phase 1 (sequential): step 1-adapter-and-registration -> step 2-finalize-and-tests
