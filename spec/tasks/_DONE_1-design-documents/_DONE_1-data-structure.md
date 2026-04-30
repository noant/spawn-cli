# 1-data-structure

## Goal
Create `spec/design/data-structure.md` describing the target repository and extension repository data structures and how their files relate.

## Approach
- Define the `target-repo` runtime tree created by the Spawn utility under `spawn/`.
- Define the `extend-repo` authoring tree under `extsrc/`.
- Explain how installing an extension copies `extsrc/` into `target-repo/spawn/.extend/{ext}/`.
- Specify `spawn/.core/config.yaml`, `spawn/navigation.yaml`, `spawn/.metadata/{ide}/rendered-mcp.yaml`, `spawn/.metadata/{ide}/rendered-skills.yaml`, ignore metadata files, extension `config.yaml`, `mcp.json`, `source.yaml`, and `spawn/rules/`.
- Document how `navigation.yaml` depends on extension config `files[].globalRead` and local `spawn/rules/` entries.
- Document how target repository folders and files depend on extension `files/`, setup scripts, static/artifact modes, and update behavior.
- Include the user-provided glob rules as the ignore-pattern contract or a concise referenced summary.

## Affected files
- `spec/design/data-structure.md`
- `spec/navigation.yaml`

## Code examples
Use YAML and tree snippets, not runtime Python code.
