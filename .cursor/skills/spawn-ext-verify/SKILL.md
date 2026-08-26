---
name: spawn-ext-verify
description: Strict check extension layout and smoke-test install in a disposable target.
---


Goal: ship only packs that pass strict validation and install cleanly.

1. From extension source root: **`spawn extension check . --strict`** — resolve missing skills, undeclared files under `extsrc/files/`, descriptions for non-no read flags, invalid or mismatched **`extsrc/mcp/*.json`** (including stray obsolete **`extsrc/mcp.json`**), missing setup scripts.
2. In a throwaway clone or empty repo: **`spawn init`**, then **`spawn extension add <path-or-url-to-your-extension-source>`** (match consumer workflow).
3. Confirm materialized paths under **`files:`** exist as expected; confirm **`artifact`** paths are not overwritten on a repeat add/update where applicable.
4. If **`healthcheck`** is configured: **`spawn extension healthcheck <name>`** from the target.
5. Document distribution: plain repo URL/path, zip, or entry in an **`extensions.yaml`** bundle for **`spawn build install`**.
6. **Version:** If this session changed **`config.yaml`**, skills, **`extsrc/files/`** layout, or **`extsrc/mcp/*.json`** in a user-visible way, **prompt** the author to bump **`version`** with **`spawn-ext-increment-version`** before tagging or releasing — unless they confirm it was docs-only typos with no behavioral impact.


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
