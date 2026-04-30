# 2-utility

## Goal
Create `spec/design/utility.md` describing how the Spawn CLI transforms a target repository and how each command and internal operation works logically.

## Approach
- Describe low-level modules: initialization, IDE list mutation, extension listing, file read metadata extraction, removable file/folder calculation, MCP parsing, raw skill parsing, skill metadata generation, navigation updates, rendered metadata updates, ignore list operations, IDE adapter calls, and extension setup script runners.
- Describe high-level modules: `refresh-gitignore`, `refresh-agent-ignore`, `refresh-skills`, `refresh-mcp`, `refresh-extension`, `remove-extension`, `install-extension`, `download-extension`, `list-extensions`, `install-build`, `add-ide`, `remove-ide`, and healthcheck.
- Describe public commands: `spawn --init`, `spawn --init --build`, `spawn --init ide ...`, `spawn --extend`, `spawn --ext --branch`, `spawn --update`, and `spawn --build`.
- Specify how extension config is interpreted during install, update, uninstall, refresh, and rebuild.
- Specify skill rebuild logic: remove previously rendered IDE skills using metadata, regenerate skill metadata from global/local read rules, render through the IDE adapter, and persist rendered paths.
- Specify MCP rebuild logic similarly.
- Propose a normalized internal MCP structure that can be rendered to different IDE formats.
- Keep the document about commands and directory transformations only; do not specify CLI argument parser implementation details beyond command semantics.

## Affected files
- `spec/design/utility.md`
- `spec/navigation.yaml`

## Code examples
Use pseudocode and normalized data shape examples where useful.
