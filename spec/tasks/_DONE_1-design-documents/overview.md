# 1: Spawn Design Documents

IMPORTANT: always use `spec/main.md` and `spec/navigation.yaml` for rules.

## Status
- [x] Spec created
- [x] Self spec review passed
- [x] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [ ] Code review passed
- [ ] HLA updated

## Goal
Create design documents that specify Spawn data layout, utility behavior, agentic flow, and extension authoring for future implementation tasks.

## Design overview
- Affected modules: `spec/design/data-structure.md`, `spec/design/utility.md`, `spec/design/agentic-flow.md`, `spec/design/extensions.md`, `spec/navigation.yaml`.
- Data flow changes: document how extension source repositories become installed target repository state under `spawn/`, how extension config drives navigation, rendered skills, MCP, ignore files, and installed files, and how CLI commands mutate that state.
- Integration points: target repository `spawn/` tree, extension repository `extsrc/` tree, IDE-specific adapters, extension setup scripts, navigation metadata, rendered metadata, gitignore and agent-ignore outputs.

## Before -> After
### Before
- Only `spec/design/hla.md` exists, and it describes the initial Python CLI package at a high level.
- There is no detailed design contract for the Spawn repository structure, extension source structure, CLI utility operations, rendered skills, MCP metadata, or AIDD extension authoring.
### After
- Four additional design documents exist under `spec/design/`.
- `spec/navigation.yaml` lists the new design documents.
- The documents define a stable conceptual basis for later implementation of initialization, extension installation, IDE rendering, rebuilds, and AIDD methodology packaging.

## Details
No blocking clarification is required because the user provided the target structures, config fields, command set, and methodology principles. The implementation should preserve the user's terms `target-repo`, `extend-repo`, `spawn/`, `extsrc/`, `extension config`, `navigation.yaml`, `rendered-skills.yaml`, and `rendered-mcp.yaml`.

Documentation must be written in English per `spec/extend/00-general.md`. Keep the design files concise but complete enough to guide future implementation. Do not implement runtime Python behavior in this task.

Key design constraints:
- The local `spawn-cli` repository must not reproduce the target repository `spawn/` runtime structure as active data; the CLI will create that structure inside a target repository.
- All paths stored in metadata, passed to methods, or returned from methods are relative to the target repository root containing `spawn/`.
- Missing metadata directories and files under `spawn/.metadata/` are created on demand.
- Extension-installed static files may be overwritten on update; artifact files and folders are preserved and may only be migrated by setup scripts.
- Extension file conflicts across installed extensions are errors before copying a new extension into `spawn/.extend/{ext}`.
- Rendered metadata exists so uninstall and refresh operations can remove only Spawn-managed IDE skills and MCP entries without touching user-managed entries.
- IDE adapters share method signatures while storing skills, MCP, and ignore data in IDE-specific formats.
- Ignore glob behavior follows the practical ignore/glob rules supplied by the user.

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions - even if a step seems trivial or small.
- Phase 1 (parallel): step `1-data-structure` || step `2-utility`
- Phase 2 (parallel): step `3-agentic-flow` || step `4-extensions`
- Phase 3 (sequential): step review - inspect all design documents, update `spec/navigation.yaml`, fix inconsistencies
