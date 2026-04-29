# 4-extensions

## Goal
Create `spec/design/extensions.md` describing how to implement an AIDD methodology as a Spawn extension in an extension repository.

## Approach
- Explain the purpose of an extension as a package for AIDD methodology files, skills, setup scripts, MCP connections, and installable files.
- Document the required and optional `extsrc/` files: `config.yaml`, `skills/*.md`, `files/**`, `setup/*.py`, `mcp.json`.
- Describe config sections: `version`, `files`, `folders`, `agent-ignore`, `git-ignore`, `skills`, and `setup`.
- Explain static versus artifact files/folders, global versus local read rules, auto versus required versus no read rules, and skill-level required-read overrides.
- Describe methodology guidance: compact core files, strict global reads, artifact evolution, static process files, contextual reads, and update-safe migration via setup scripts.
- Describe how to create an extension from existing `spawn/rules` in a target repository.
- Describe build extensions and build manifests through `extensions.yaml`.
- Include publishing considerations only at the design level, including future reuse of the existing PyPI publish script pattern for the `spawn-cli` package.

## Affected files
- `spec/design/extensions.md`
- `spec/navigation.yaml`

## Code examples
Use example `extsrc/config.yaml`, `extensions.yaml`, and tree snippets.
