---
name: spawn-ext-bootstrap
description: Bootstrap a new Spawn extension repo with extsrc skeleton and stable id.
---


Goal: start a new Spawn extension (methodology pack) from zero or from an existing repo that lacks `extsrc/`.

1. Confirm or choose extension id (`name`): kebab-case, stable across releases; decide initial `version` string.
2. From the extension repo root run `spawn extension init . --name <id>` so `extsrc/` and `config.yaml` exist.
3. Set `schema: 1`, `name`, `version` in `config.yaml`; remove empty stub keys you will not use yet if the tool allows, or leave minimal valid maps.
4. Plan top-level namespaces under `extsrc/files/` (e.g. `my-org/spec/`, `my-org/guides/`) so paths do not collide with other extensions in combined targets.
5. Next steps: use sibling skills to declare **`files`** / **`folders`**, add templates under **`extsrc/files/`**; MCP lives under **`extsrc/mcp/*.json`** (see **spawn-ext-mcp**); then **`spawn extension check . --strict`**.
6. **Later:** whenever packaging meaningfully evolves after bootstrap, **prompt** a **`version`** bump using **`spawn-ext-increment-version`** before publishing (initial `0.1.0` or `1.0.0` is typical until first stable story).


Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.
- Use the platform ask tool when available (R10-ask in spec/main.md); otherwise, stop and request input from the user.

Mandatory reads:
- `spawn-ext-guide/ai/core.md` - Machine baseline — terms, extsrc tree rules, static vs artifact, name and uniqueness, install outputs.
- `spawn-ext-guide/ai/cli.md` - Machine CLI reference — spawn init/extension/build commands, extensions.yaml bundle shape, authoring checklist.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spawn-ext-guide/ai/config-yaml.md` - Machine schema for config.yaml — keys, files/folders/skills modes, reads, ignores, setup, annotated example.
- `spawn-ext-guide/ai/skill-sources.md` - Machine rules for extsrc/skills/*.md — frontmatter, name/description resolution, rendered skill shape, example.
- `spawn-ext-guide/ai/mcp-json.md` - Machine schema for extsrc/mcp/windows.json, linux.json, macos.json — servers, OS selection, aligned name sets, transport, spawn_stdio_proxy (stdio IDE proxy), env, capabilities, validation against check, JSON examples.
- `spec/main.md` - Spec-Tasks methodology — folder structure, seven-step process, overview template.
- `spec/design/hla.md` - Project high-level architecture; updated in Step 7.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
