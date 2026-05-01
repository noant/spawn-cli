# IDE Adapters

This document defines how Spawn renders extension metadata into concrete IDE
surfaces: MCP configuration, skills or rule files, agent entry points, and
agent ignore files. It complements `spec/design/utility.md`; the utility owns
the lifecycle, while this document owns adapter-specific targets and shape
conversion.

The paths below are the initial adapter contract. Some IDE formats change
quickly, so each adapter must implement `detect()` rather than silently assuming
an IDE layout. Install-time and extension-driven refresh warnings when skills or MCP
capabilities are insufficient are handled by the utility layer (`add-ide`,
`_refresh_extension_core`, `refresh_extension_for_ide` when “the gap matters”),
not by a free-form warning list on `detect()` itself.

## Adapter Registry

The canonical IDE key **order and membership** are defined by **one frozen
constant in source code** (see `spec/design/utility.md`, Supported IDE keys). There
are **no** environment variables or config files that alter this list.
`supported_ide_keys()` returns that constant; the adapter registry must register
a **concrete** adapter for every canonical key. User-facing aliases are handled only when parsing
CLI arguments before `ide.Get(name)`.

Supported names (canonical):

- `cursor`
- `codex`
- `claude-code`
- `windsurf`
- `github-copilot`
- `gemini-cli`

Additional IDE layouts (Qoder, Qwen Code, Aider, Zed, Devin) are described later
in this document for future adapters; they are **not** CLI-supported until added
to `CANONICAL_IDE_KEYS` with a full implementation.

Aliases are normalized before lookup:

```text
claude -> claude-code
gemini -> gemini-cli
copilot -> github-copilot
github -> github-copilot
```

Unknown names are errors. Unsupported operations on a known adapter are
warnings and leave Spawn metadata unchanged for that operation.

## Common Adapter Interface

Every adapter exposes the same logical operations:

```text
detect(targetRoot) -> DetectResult
add_skills(targetRoot, skillMetadata[]) -> RenderedPath[]
remove_skills(targetRoot, renderedPaths[]) -> void
add_mcp(targetRoot, normalizedMcp) -> RenderedMcpName[]
remove_mcp(targetRoot, renderedMcpNames[]) -> void
add_agent_ignore(targetRoot, globs[]) -> void
remove_agent_ignore(targetRoot, globs[]) -> void
rewrite_core_agent_ignore(targetRoot, globs[]) -> void   # optional; native IDEs
rewrite_extension_agent_ignore(targetRoot, globs[]) -> void
clear_spawn_agent_ignore(targetRoot) -> void
rewrite_entry_point(targetRoot, prompt) -> RenderedPath | warning
```

`DetectResult` contains:

```yaml
used-in-repo: true
capabilities:
  skills: native
  mcp: project
  agentIgnore: native
  entryPoint: agents-md
```

`used-in-repo` is a single boolean: whether the repository already shows typical
IDE project footprint or usage signals for this adapter (config dirs, marker
files, etc.). It replaces separate availability, confidence, and ad hoc warning
lists from earlier drafts.

Spawn evaluates skill and MCP capability limits **outside** ``detect()``,
before utility-layer refresh orchestration (**`add-ide`**, **`_refresh_extension_core`**,
and **`refresh_extension_for_ide`**) :

- If `capabilities.skills` is insufficient for Spawn's intended skill rendering
  (`unsupported`, or another value documented by the adapter as degraded),
  Spawn prints a **warning** before running refresh **when installed extensions expose skill files**.
- If `capabilities.mcp` is insufficient for repository-scoped MCP rendering
  (`unsupported`, or documented degraded values such as `external` when no
  safe project target exists), Spawn prints a **warning** before running refresh
  **when the merge would touch MCP servers** (predicate scope matches that path:
  aggregation for `add-ide`, the core call’s extension for `_refresh_extension_core`,
  the named extension for `refresh_extension_for_ide`).

Those **`SpawnWarning`** lines are emitted at most once per IDE per invocation
when the gap matters; adapter internals may still emit other warnings inside
individual operations.

Capability values:

- `native`: the IDE has a first-class project feature for this surface.
- `project`: Spawn can write a project-scoped config consumed by the IDE.
- `entry-only`: Spawn injects guidance into the entry point instead of a
  native skill or rule system.
- `external`: configuration exists outside the repository; Spawn must warn
  before mutating user-level state and should prefer project-level state.
- `unsupported`: the adapter does not render this surface.

## Spawn Metadata Inputs

Adapters consume normalized Spawn metadata, not extension source files.

Skill metadata:

```yaml
name: spectask-execute
description: Execute approved spectasks.
content: "Skill body without optional notation."
hints:
  - Prefer spectask steps in order.
required-read:
  - file: spec/main.md
    description: Spec task process.
auto-read:
  - file: spec/design/hla.md
    description: Project high-level architecture.
```

`SkillMetadata.hints` carries plain-text hint strings (possibly empty): **`hints.global` from every installed extension** plus **`hints.local` for the owning pack** plus maintainer **`read-required` rule** hints (`generate_skills_metadata`). IDE Markdown rendering lists them in a **Hints:** section **after** the skill body and **before** **Mandatory reads** (`spawn_cli.ide._helpers.render_skill_md`).

MCP metadata:

```yaml
servers:
  - name: spectask-search
    extension: spectask
    transport:
      type: stdio
      command: uvx
      args:
        - spectask-search-mcp
      cwd: .
    env:
      SPECTASK_TOKEN:
        source: user
        required: true
        secret: true
    capabilities:
      tools: true
      resources: false
      prompts: false
```

The entry point prompt is generated once by Spawn core and passed to every
adapter. It must tell the agent to read `spawn/navigation.yaml`, read all
`read-required` entries, and choose `read-contextual` entries by task relevance.
When **`rollup_hints_for_agents`** returns non-empty hints, the prompt also
includes a **Hints:** bullet list (full text; warnings only, no truncation).

## IDE Matrix

| IDE | Skills / rules target | MCP target | Agent ignore target | Entry point | Notes |
| --- | --- | --- | --- | --- | --- |
| Cursor | `.cursor/skills/{skill}/SKILL.md`; Project Rules `.cursor/rules/*.md`/`.mdc` | `.cursor/mcp.json`; other MCP JSON under `.cursor/` as detected | `.cursorignore` (repo root) | `AGENTS.md` | Rules and Skills are parallel mechanisms; legacy `.cursorrules` deprecated vs `.cursor/rules`. (Cursor also discovers other tools’ skill dirs for compatibility—outside this column.) |
| Codex | `.agents/skills/{skill}/SKILL.md` | `.codex/config.toml` | — | `AGENTS.md` | OpenAI documents repo skills under `.agents/skills/` (not under `.codex/`). Requires trusted workspace for project `.codex/` layers. |
| Qoder | `.qoder/skills/{skill-name}/SKILL.md` | `.mcp.json` | `.qoder/settings.json` `permissions` (and optional `hooks` in the same files) | `AGENTS.md` | `.qoder/rules` in-repo can supersede `.qoder`/memory behavior per Qoder IDE docs. |
| Claude Code | `.claude/skills/{skill}/SKILL.md` | `.mcp.json` (repository root) | `.claude/settings.json` (`permissions.*`) | `CLAUDE.md` or `.claude/CLAUDE.md` | Spawn metadata/removal for MCP keyed by server name. |
| Qwen Code | `.qwen/skills/{skill}/SKILL.md` | `.qwen/settings.json` `mcpServers` | `.qwen/settings.json` `permissions`; root `.qwenignore` | `QWEN.md` | Project settings file is repo-root `.qwen/settings.json`. |
| Windsurf | `.windsurf/skills/{skill}/SKILL.md`; `.windsurf/rules/{name}.md` | — (no documented committed project MCP schema on Cascade MCP docs) | `.codeiumignore` (workspace root) | `AGENTS.md` | MCP is historically user-global; Spawn may still run `detect()` for future or in-app repo targets. |
| GitHub Copilot | `.github/skills/{skill}/SKILL.md` (agent skills); `.github/instructions/{name}.instructions.md` (path instructions, `applyTo`) | `.vscode/mcp.json` | — | `.github/copilot-instructions.md`; `AGENTS.md` | Repo instruction layers and optional `.github/prompts/*.prompt.md` (manual). |
| Aider | `CONVENTIONS.md` plus `.aider.conf.yml` `read:` | — | `.aiderignore` (git root default) | `CONVENTIONS.md` | No IDE-style hierarchical skills; conventions are read-only context. |
| Zed | `AGENTS.md`, `.rules`, `CLAUDE.md`, … per Zed rules doc | `.zed/settings.json` `context_servers` | `agent.tool_permissions` / workspace scan exclusions in settings (no `.cursorignore` equivalent) | `AGENTS.md` | MCP key name is `context_servers`. (Upstream may add repo skills under other paths—outside this column until documented.) |
| Gemini CLI | `.gemini/skills/{skill}/SKILL.md` | `.gemini/settings.json` `mcpServers` | `.geminiignore` | `GEMINI.md` (unless overridden via `context.fileName`) | Project `.gemini/settings.json` at repo root. (CLI may also merge `.agents/skills/` discovery—outside this column.) |
| Devin | `.devin/skills/{skill}/SKILL.md` | `.devin/config.json` `mcpServers` | — | `AGENTS.md` | Imports from other tooling may merge MCP at runtime (`read-config-from`)—outside committed files unless copied. (Optional Spawn-only trees are not part of this matrix.) |

## Skill Rendering

Adapters must preserve the same semantic content:

1. Skill name and description.
2. Original skill body (extension source markdown after frontmatter).
3. **Hints** bullets from `SkillMetadata.hints`, when non-empty, **after** the body and **before** mandatory reads.
4. Mandatory reads: merged `required-read` paths plus `spawn/navigation.yaml` exactly once, always the last mandatory bullet.
5. Contextual reads from `auto-read`.

### Markdown Skill Shape

Used by Cursor, Codex, Qoder, Claude Code, Qwen Code, and Gemini CLI when the
IDE supports directory skills. Codex discovers project skills under
`.agents/skills/` (not `.codex/skills/`); see OpenAI Codex documentation.

```text
{skill-root}/{skill-name}/
  SKILL.md
```

`SKILL.md`:

```markdown
---
name: spectask-execute
description: Execute approved spectasks.
---

{source skill content}

Hints:
- Short plain-text reminder when `hints` metadata is non-empty.

Mandatory reads:
- `spec/main.md` - Spec task process.
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spec/design/hla.md` - Project high-level architecture.
```

Adapters that do not support frontmatter should remove the frontmatter and keep
the same fields as plain Markdown.

### Cursor Native Skill Shape

Cursor uses native Agent Skills in the editor and CLI. Spawn renders each
normalized skill as:

```text
.cursor/skills/{skill-name}/
  SKILL.md
```

Spawn maps skills for the `cursor` adapter **only** to `.cursor/skills/{skill-name}/` (matches the IDE Matrix above). Cursor itself may merge other directories at runtime—the adapter does not duplicate those layouts.

The file uses the common Markdown skill shape above. If a Cursor version
requires additional skill package files, `detect()` should report the detected
format and the adapter should add only deterministic Spawn-owned files inside
that skill directory.

### Cursor MDC Fallback Shape

Cursor rules (`.cursor/rules/*.md` or `.mdc` with frontmatter) are a parallel
surface to Agent Skills: use rules for persistent, conditionally applied
instructions; use skills for packaged workflows. Spawn may still render skills
as MDC rules when a feature needs always-on declarative guidance rather than
procedural skill directories. Fallback rules are rendered as project rules:

```markdown
---
description: Execute approved spectasks.
alwaysApply: false
---

# spectask-execute

{skill body}

Hints:
- Short reminder when hints exist.

Mandatory reads:
- ...
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

...
```

Spawn uses `alwaysApply: false` for fallback skill rules so the rule is
available by description rather than injected into every request. Required
global context is still handled by the entry point and `spawn/navigation.yaml`.

### GitHub Copilot Instructions Shape

GitHub Copilot **path-specific instructions** use one Markdown file per
instruction set (often `.github/instructions/{name}.instructions.md`):

```markdown
---
applyTo: "**"
---

# spectask-execute

Description: Execute approved spectasks.

{skill body}

Hints:
- Short reminder when hints exist.

Mandatory reads:
- ...
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

...
```

The root `.github/copilot-instructions.md` contains only the Spawn-managed
entry block. Path-specific instructions live under `.github/instructions/`
(tracked independently in `rendered-skills.yaml` when Spawn maps skills to that
surface). Repository **Agent Skills** (`SKILL.md` under `.github/skills/`) use
the common Markdown skill shape and are tracked separately—do not confuse with
`*instructions*.md`.

### Aider Consolidated Shape

Aider does not have native discoverable skills. Spawn renders:

- `CONVENTIONS.md` with the entry point block and compact list of rendered
  skills;
- `.aider.conf.yml` with `read: CONVENTIONS.md` or merged `read` entries.

The adapter records both files in `rendered-skills.yaml` when it mutates them.

## MCP Rendering

Spawn normalizes MCP once and each adapter maps transport fields into the IDE
schema.

### Generic JSON MCP Shape

This shape uses top-level **`mcpServers`** (same family as Claude Code’s project
`.mcp.json`): for example Cursor `.cursor/mcp.json`, Claude Code repository
root `.mcp.json`, and Qoder when writing repo-root `.mcp.json`.

VS Code / GitHub Copilot Agent mode uses a **different** workspace file shape:
top-level **`servers`** plus optional **`inputs`** in `.vscode/mcp.json` (see [VS Code MCP configuration](https://code.visualstudio.com/docs/copilot/reference/mcp-configuration)).
Do not mix the two schemas in one file.

```json
{
  "mcpServers": {
    "spectask-search": {
      "command": "uvx",
      "args": ["spectask-search-mcp"],
      "env": {
        "SPECTASK_TOKEN": "${SPECTASK_TOKEN}"
      }
    }
  }
}
```

For HTTP-like transports:

```json
{
  "mcpServers": {
    "spectask-search": {
      "type": "streamable-http",
      "url": "https://example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${SPECTASK_TOKEN}"
      }
    }
  }
}
```

Secrets are placeholders only. Spawn must not write actual secret values.

### VS Code / Copilot MCP Shape

VS Code Copilot Agent mode uses `.vscode/mcp.json`:

```json
{
  "servers": {
    "spectask-search": {
      "type": "stdio",
      "command": "uvx",
      "args": ["spectask-search-mcp"],
      "env": {
        "SPECTASK_TOKEN": "${input:spectask-token}"
      }
    }
  },
  "inputs": [
    {
      "id": "spectask-token",
      "type": "promptString",
      "description": "SPECTASK_TOKEN",
      "password": true
    }
  ]
}
```

If an environment variable is marked `secret: true`, the adapter should prefer
an input or IDE secret reference over a literal placeholder when supported.

### Qwen / Gemini Settings Shape

Qwen Code and Gemini CLI project settings use `mcpServers`:

```json
{
  "mcpServers": {
    "spectask-search": {
      "command": "uvx",
      "args": ["spectask-search-mcp"],
      "env": {
        "SPECTASK_TOKEN": "${SPECTASK_TOKEN}"
      }
    }
  }
}
```

For HTTP:

```json
{
  "mcpServers": {
    "spectask-search": {
      "httpUrl": "https://example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${SPECTASK_TOKEN}"
      }
    }
  }
}
```

When both `url` and `httpUrl` are accepted by the tool, Spawn renders
`httpUrl` for streamable HTTP and `url` for SSE.

### Zed Context Server Shape

Zed registers MCP servers under **`context_servers`** in settings JSON (often
merged into project `.zed/settings.json`). Stdio servers use `command`, `args`,
and `env`; remote servers use `url` with optional `headers`. If remote auth is
missing, Zed may prompt for MCP OAuth instead of failing immediately—see [Zed
MCP](https://zed.dev/docs/ai/mcp).

```json
{
  "context_servers": {
    "spectask-search": {
      "command": "uvx",
      "args": ["spectask-search-mcp"],
      "env": {
        "SPECTASK_TOKEN": "${SPECTASK_TOKEN}"
      }
    }
  }
}
```

For remote servers:

```json
{
  "context_servers": {
    "spectask-search": {
      "url": "https://example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${SPECTASK_TOKEN}"
      }
    }
  }
}
```

### Codex TOML Shape

Codex uses TOML configuration. Hyphenated server names must use **quoted** table
keys; unquoted `spectask-search` is invalid TOML (parsed as subtraction).

```toml
[mcp_servers."spectask-search"]
command = "uvx"
args = ["spectask-search-mcp"]

[mcp_servers."spectask-search".env]
SPECTASK_TOKEN = "${SPECTASK_TOKEN}"
```

For HTTP:

```toml
[mcp_servers."spectask-search"]
url = "https://example.com/mcp"
```

If project-level Codex config is skipped (e.g. workspace not trusted) or
unsupported by the installed Codex build, the adapter reports that user-level
config requires explicit approval.

## Entry Point Rendering

Entry point files are user-visible and may already contain user instructions.
Adapters must update only a Spawn-managed block when possible:

```markdown
<!-- spawn:start -->
Before working, read `spawn/navigation.yaml`.
Read every file listed under `read-required`.
Inspect `read-contextual` descriptions and read only files relevant to the
current task.

Hints:
- Example maintainer or extension-global reminder.
<!-- spawn:end -->
```

If the IDE requires a whole-file entry point, the adapter must warn before
overwriting. The warning should name the file and recommend backing up user
content or moving it outside the Spawn-managed block.

Entry point targets:

| IDE | Entry file |
| --- | --- |
| Cursor | `AGENTS.md` |
| Codex | `AGENTS.md` |
| Qoder | `AGENTS.md` |
| Claude Code | `CLAUDE.md` |
| Qwen Code | `QWEN.md` |
| Windsurf | `AGENTS.md` |
| GitHub Copilot | `.github/copilot-instructions.md` and root `AGENTS.md` |
| Aider | `CONVENTIONS.md` |
| Zed | `AGENTS.md` |
| Gemini CLI | `GEMINI.md` |
| Devin | `AGENTS.md` |

Gemini CLI additionally reads which context filenames to load via `context.fileName` under the `context` section in `.gemini/settings.json` (a string or array; default behavior still centers on `GEMINI.md` unless changed).

## Agent Ignore Rendering

Agent ignore support is uneven. Spawn always maintains `.gitignore` separately
through the core gitignore lifecycle. IDE agent ignore rendering is adapter
specific and must not pretend to work when there is no supported target.

| IDE | Agent ignore behavior |
| --- | --- |
| Cursor | Merge Spawn-owned globs into `.cursorignore` when present or supported. Terminal/MCP may still reach paths not covered by ignores. |
| Codex | Unsupported dedicated agent-ignore file (`/.codexignore` not upstream); steer via AGENTS/policy. |
| Qoder | Use `.qoder/settings.json` permissions allow/ask/deny with gitignore-style path patterns (and hooks co-located in the same JSON). |
| Claude Code | Prefer `permissions.*` and related keys in `.claude/settings.json` over undocumented single-file ignore semantics. |
| Qwen Code | Use `permissions` rules (`deny` / `ask` / `allow`) for tool and path blocking; optionally merge Spawn globs into `.qwenignore` for search-scope reduction — not interchangeable with Cursor-style ignores. |
| Windsurf | Use `.codeiumignore` (and optional global under `~/.codeium/`); rules alone do not replicate ignore semantics. |
| GitHub Copilot | GitHub Copilot content exclusion does not apply to IDE Agent mode; no Spawn-target “agent ignore” file—instructions and policies only. |
| Aider | Use `.aiderignore` only when supported by installed version. |
| Zed | No Cursor-style `.cursorignore`; approximate exclusions via scan settings and `agent.tool_permissions`. |
| Gemini CLI | Merge Spawn-owned globs into `.geminiignore`. |
| Devin | Spawn does not assume a writable ignore-file contract; Terminal may expose `respect_gitignore` for tools only. |

When an adapter renders ignore globs into a file that also contains user globs,
it must use a managed block or an ownership metadata comparison so uninstall
removes only Spawn-owned entries.

## Ownership Records

Adapters return concrete rendered paths and server names to the utility layer.
The utility then writes:

- `spawn/.metadata/{ide}/rendered-skills.yaml`
- `spawn/.metadata/{ide}/rendered-mcp.yaml`
- `spawn/.metadata/{ide}/agent-ignore.txt`

Adapter code must not write these metadata files directly. This keeps
rendering side effects separate from Spawn ownership state.

## Removal Semantics

`remove_skills` receives exact paths from metadata and deletes only those paths.
If a rendered skill directory becomes empty after deleting `SKILL.md`, the
adapter may remove the empty directory.

`remove_mcp` receives server names from metadata and removes only those MCP
entries. If the containing config file has no user content and was created by
Spawn, the adapter may leave an empty valid config file rather than deleting it.

`remove_agent_ignore` removes only globs recorded as Spawn-owned for that IDE.

## Error And Warning Rules

Errors stop before mutation when:

- the adapter name is unknown;
- a target path escapes the repository root;
- a rendered path is owned by another installed extension;
- a config file is syntactically invalid and cannot be safely merged;
- an unsupported config schema would require deleting user content.

Warnings allow the command to continue when:

- an IDE is not installed but project files can still be rendered;
- MCP is unsupported for the adapter;
- a skill surface is emulated through entry point or rules;
- user-level config would be required and approval was not granted;
- an adapter target is known to be version-dependent.

## Implementation Notes

Use structured parsers for JSON, YAML, TOML, and frontmatter. Do not parse
adapter config files with ad hoc string slicing.

All adapter writes must be deterministic: stable key ordering where practical,
stable filenames, and idempotent managed blocks.

Rendered filenames should use normalized skill names:

```text
lowercase, trim, replace spaces with "-", keep [a-z0-9._-], collapse repeats
```

Render-Time uniqueness is enforced **before** adapters run (`utility.md`,
Cross-extension rendered identity). If two extensions would use the same
normalized skill name in the same IDE target, Spawn errors; adapters **must not**
apply automatic `{extension}-{skill}` namespacing to paper over clashes.

Overwriting a destination that is **Spawn-owned by the same extension** in
metadata may still warn per command policy; collisions with **user-owned** paths
outside Spawn metadata remain errors per Error And Warning Rules above.
