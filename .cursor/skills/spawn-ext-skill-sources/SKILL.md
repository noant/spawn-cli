---
name: spawn-ext-skill-sources
description: Author extsrc/skills and register them in config with required-read merges.
---


Goal: add or change agent skills shipped with the extension.

1. Add `extsrc/skills/<skill-key>.md` (UTF-8 Markdown). Filename must match the key under `skills:` when declared.
2. Prefer short procedural bodies; long reference belongs under `extsrc/files/` and is linked via `localRead`/`globalRead` or per-skill `required-read`.
3. Optional YAML frontmatter with `name` and/or `description`; otherwise set them under `skills:` in `config.yaml` (config overrides frontmatter where both apply per resolution rules).
4. Under `skills:` list `required-read` target paths only when they are mandatory for that skill beyond merged global/local rules; avoid pointless duplication.
5. After normalization, skill display names must remain unique across all extensions installed in one target — use a stable prefix.
6. Run `spawn extension check . --strict` after adding or renaming skill files.
7. **Version:** Adding, removing, or materially changing skills or their **`required-read`** affects consumers — **prompt** the author to bump **`version`** via **`spawn-ext-increment-version`** before release (unless the change is typo-only text with no behavior impact).


Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.
- Use the platform ask tool when available (R10-ask in spec/main.md); otherwise, stop and request input from the user.

Mandatory reads:
- `spawn-ext-guide/ai/core.md` - Machine baseline — terms, extsrc tree rules, static vs artifact, name and uniqueness, install outputs.
- `spawn-ext-guide/ai/config-yaml.md` - Machine schema for config.yaml — keys, files/folders/skills modes, reads, ignores, setup, annotated example.
- `spawn-ext-guide/ai/skill-sources.md` - Machine rules for extsrc/skills/*.md — frontmatter, name/description resolution, rendered skill shape, example.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spawn-ext-guide/ai/mcp-json.md` - Machine schema for extsrc/mcp/windows.json, linux.json, macos.json — servers, OS selection, aligned name sets, transport, spawn_stdio_proxy (stdio IDE proxy), env, capabilities, validation against check, JSON examples.
- `spawn-ext-guide/ai/cli.md` - Machine CLI reference — spawn init/extension/build commands, extensions.yaml bundle shape, authoring checklist.
- `spec/main.md` - Spec-Tasks methodology — folder structure, seven-step process, overview template.
- `spec/design/hla.md` - Project high-level architecture; updated in Step 7.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
