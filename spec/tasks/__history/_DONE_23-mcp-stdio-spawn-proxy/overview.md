# 23: Stable IDE MCP rendering via `spawn mcp_stdio` stdio proxy

## Source seed
- Path: none

## Status
- [V] Spec created
- [V] Self spec review passed
- [V] Spec review passed
- [V] Code implemented
- [V] Self code review passed
- [V] Code review passed
- [V] Design documents updated

## Goal
For extension MCP servers that opt into stdio indirection, render IDE MCP config as a stable `spawn mcp_stdio extension … name …` invocation while resolving OS-specific transport and proxying MCP stdio only at runtime.

## Design overview
- Affected modules: `spawn_cli.models.mcp`; `spawn_cli.core.low_level` (MCP JSON parsing / `list_mcp`); `spawn_cli.core.high_level` (`extension_check` rules for MCP); new small module or `spawn_cli.core` submodule for subprocess stdio bridging; `spawn_cli.cli` (new `mcp_stdio` command group); every `IdeAdapter.add_mcp` implementation that emits stdio entries (`cursor.py`, `claude_code.py`, `gemini_cli.py`, Copilot VS Code adapter, Codex if applicable, Zed/other stdio-capable adapters in tree); tests under `tests/`.
- Data flow changes: Authored **`servers[]`** entries in `extsrc/mcp/{windows,linux,macos}.json` may set a boolean **`spawn_stdio_proxy`**. When true and `transport.type` is **`stdio`**, normalization keeps full per-host transport data for runtime. IDE adapters **`add_mcp`** behave like today’s **`stdio`** path for **every emitted field** (`type`, **`cwd`**, **`env`/placeholders/`inputs`** wiring per IDE schema), **except** **`command`** and **`args`** are replaced by the Spawn wrapper (**`command`** = Spawn entry-point, **`args`** = `["mcp_stdio","extension","<extension>","name","<server.name>"]`). That swaps only **`command`/`args`**, so OS-specific binaries are omitted from IDE files (**cross-platform rationale**). **`spawn mcp_stdio`** resolves `spawn/` root from **`Path.cwd()`**, loads **`list_mcp`** for the current host OS, selects the server by **`name`**, then starts the inner stdio MCP using **`transport.command`**, **`args`**, **`cwd`**, and resolved **`env`**, proxies **stdin/stdout** for MCP framing, **`stderr`** per **CLI proxy implementation details** below. Non-stdio transports must not use the flag (**strict `extension_check`** error).
- Integration points: `refresh_mcp` path unchanged (`adapter.add_mcp` consumes `NormalizedMcp`). Design docs (**Step 7**): **`spec/design/ide-adapters.md`**, **`extension-author-guide.md`**, **`extensions.md`**, **`utility.md`** / **`utility-method-flows.md`** as needed; **`spec/design/hla.md`** one-line CLI mention if warranted.

## Before → After
### Before
- IDE-rendered MCP for stdio uses concrete **`command`** / **`args`** (and often **`cwd`**) from **`list_mcp`**, so differing OS transports force different merged IDE files unless teams maintain separate clones or regenerate per machine.
### After
- Opt-in servers keep the **same rich IDE MCP entry shape** adapters already produce for **`stdio`** (including **`cwd`**, **`env`**, schema-specific knobs), except **`command`/`args`** launch **`spawn mcp_stdio …`** instead of inlining **`transport.command`/`args`**. **`spawn mcp_stdio`** reads **`mcp/{windows|linux|macos}.json`** on the machine it runs on and proxies MCP stdin/stdout to the resolved inner server.

## Details
### Authoring (`servers[]` object)
- Required when proxying: **`name`**, **`transport.type`** = **`stdio`**, **`transport.command`**, and any other fields required today for valid stdio.
- **`spawn_stdio_proxy`**: **`true`** enables IDE indirection described above (default **`false`** preserves today’s inline stdio emission).
- **HTTP/SSE/other** transport with **`spawn_stdio_proxy`** true **`->`** **`extension_check` error** (strict and non-strict where applicable consistent with repo rules).

### Resolved inner process (runtime only)
- **Working directory**: inner **`cwd`** follows **`McpTransport.cwd`** semantics relative to the **managed repository root** (same as adapters use today when writing **`cwd`** into IDE MCP config).
- **Environment**: the **IDE** still launches **`spawn`** with **`env`/placeholders** exactly as adapters render today; **`spawn mcp_stdio`** must (**Step 4**) ensure the **inner** MCP process receives the **`env`** implied by authored **`env`** (**`McpEnvVar`**) merged with **`os.environ`** consistently with non-proxy **`stdio`** so secrets resolved by the IDE onto the **`spawn`** process propagate to **`os.environ`** for child resolution (**do not silently drop authored env**).

### CLI surface (normative UX)
```
spawn mcp_stdio extension <extension_id> name <server_name>
```
- **`extension_id`**: installed extension directory name under **`spawn/.extend/`** (`list_extensions`).
- **`server_name`**: matches **`servers[].name`** in platform JSON files (same cardinality across **`windows`/`linux`/`macos`** as today).
- **Exit codes**: forward inner process exit when possible; **SpawnError** for missing **`spawn/`**, unknown extension/server, unsupported transport selection, subprocess start failure.

### IDE adapter contract
- For **`stdio`** servers with **`spawn_stdio_proxy`** true: **`add_mcp`** output must match the **`stdio`** branch of that adapter (**type**, **`cwd`**, **`env`**, **`inputs`/headers** parity) byte-for-byte in structure **except** replacement of **`command`** and **`args`** by the Spawn wrapper (**Step 4** verifies with adapter-level tests/snippets).

### CLI proxy implementation details (what Point 3 referred to — normative targets for Step 2)
These are orthogonal to **`env`/adapter rendering**; they govern **whether the MCP subprocess works reliably** inside the IDE.
1. **Repository lock (`spawn_lock`)**: Today many mutating Spawn commands serialize on **`spawn_lock`**. **`mcp_stdio`** is a **long‑lived** stdio relay; taking the **same exclusive lock** as **`spawn refresh`** would **block Refresh** until the MCP session exits (often never). Prefer **`mcp_stdio` does not acquire `spawn_lock`** (read-only **`list_mcp`** + **`Path`**/`JSON` reads only). Document if an exception applies.
2. **Stdio vs stderr**: MCP **JSON-RPC** rides on **stdin/stdout** together with the spawned child; **`stderr`** is **not** the protocol channel. Prefer **transparently forward inner process `stderr`** to **`spawn`**’s **`stderr`** (then to the IDE) so server logs/errors remain visible; avoid merging **`stderr`** into **`stdout`**.
3. **Buffering/framing**: Use **binary‑safe, unbuffered** pipe forwarding (avoid **text mode** or **Python line buffering**) so JSON-RPC **Content-Length / NDJSON streams** are not truncated or chunked incorrectly.

### Implementation details

#### JSON authoring and normalization
- **Key**: **`spawn_stdio_proxy`** beside **`servers[]`** items (same level as **`name`** / **`transport`**). Omit -> **`False`**. **`true`/`false`** only (reject non-boolean with the same MCP parse error UX as malformed server objects).
- **Parser**: extend **`spawn_cli.core.low_level._normalized_mcp_from_loaded`** (**or helper it calls**) to read the flag into **`McpServer.spawn_stdio_proxy`**.
- **`list_mcp`** stays one platform file per call; callers always receive **transport + proxy flag coherently for the host OS**.

#### **`extension_check`** (**`spawn_cli.core.high_level`**)
- **`spawn_stdio_proxy`** and **`transport.type` != **`stdio`** -> message names both fields; obey existing **strict** vs loose warning pattern used for MCP layout errors.
- **Optional**: if **`proxy`** true and **`transport.command`** absent/empty -> same error path as plain invalid stdio (do not weaken checks).

#### CLI: parser shape (`spawn_cli.cli`)
Normative nesting (argparse **`add_subparser`** chain):
1. Top-level **`mcp_stdio`** (**`spawn mcp_stdio ...`**).
2. Sub-parser **`extension`** (**literal**) with positional **`extension_id`** (installed directory name under **`spawn/.extend/`**, same spelling as **`list_extensions`**).
3. Sub-parser **`name`** (**literal**) with positional **`server_name`** (**`servers[].name`**).

Provide **`help`/`description`** strings suitable for **`spawn mcp_stdio -h`** and extension authors copying from docs.

#### CLI: **`main`** / **`_dispatch`** and repository locks (critical)
Current **`_dispatch`** path: after **`init`**, every command runs **`with spawn_lock(target_root):`**. **`mcp_stdio`** is excluded:
- **`_dispatch`** (or **`main`**) recognizes **`cmd == "mcp_stdio"`** immediately after **`_require_init`** and calls a dedicated **`_dispatch_mcp_stdio(args, target_root) -> int`** **without entering** **`spawn_lock`**.
- **`_require_init`** remains so the command only runs inside an initialized Spawn repo (**`spawn/`** exists).

Rationale recap: MCP sessions are long-lived; the global repo lock must not block **`spawn refresh`** (or other mutations) until the MCP process exits.

#### Runtime module (**suggested**) 
- **`spawn_cli.core.mcp_stdio`** (filename illustrative) exposes **`run_mcp_stdio_proxy(target_root, extension_id, server_name) -> int`** (**process exit code**), or **`NoReturn`**-style relay that **`sys.exit`s** mirror child — implementation chooses one style; callers from **`cli`** wrap in **`try`/`SpawnError`** as elsewhere.

Resolution sequence:
1. **`extension_id in ll.list_extensions(target_root)`** else **`SpawnError`**.
2. **`nm = ll.list_mcp(target_root, extension_id)`**.
3. Find **`srv`** with **`srv.name == server_name`**.
4. If **`not srv.spawn_stdio_proxy`**: **`SpawnError`** must mention **`spawn_stdio_proxy: true`** for that server's object (installed **`spawn/.extend/{extension_id}/mcp/{platform}.json`**, or authoring **`extsrc/mcp/`** plus reinstall/`refresh`).
5. If **`srv.transport.type != "stdio"`** or **`transport.command`** missing: **`SpawnError`** (unexpected if authoring passes **`extension_check`**).

Inner launch:

- **`cwd`**: **`(target_root / srv.transport.cwd).resolve()`** for repo-relative authoring; effective directory **must equal** inlined **`stdio`** for the same **`McpServer`** (**verify against each adapter **`cwd`** write path**).
- **`env`**: start **`dict(os.environ)`**, overlay string mappings derived from **`srv.env`** (**`McpEnvVar`**) via **one helper** (name up to Step 4) so inner env equals inlined **`stdio`** plus IDE-injected vars. Prefer refactoring adapters onto the helper when scope stays small.
- **`Popen`**: **`[srv.transport.command, *srv.transport.args]`** (**no shell**); **`stdin=sys.stdin.buffer`**, **`stdout=sys.stdout.buffer`** (**do not attach MCP framing through **`stdin=PIPE`** on the session stream**); prefer **`stderr` inherited**.

Stdio / stderr bridging:
- Bidirectional MCP traffic: blocking **`read`** / **`write`** loops (**two daemon threads**: parent **`stdin` -> child `stdin`**, child **`stdout` -> parent `stdout`**) or **`asyncio`** `StreamReader` pairs if codebase already favors it; **never** Unicode text-mode transforms on MCP byte streams (**`sys.stdin.buffer`**, **`bufsize=0`** where **`Popen`** supports it).
- **stderr**: default **inherit child stderr** (**`stderr=None`** in **`Popen`**) vs parent **unless** mirrored copy proves necessary for a host IDE.
- Child termination: monitor wait; propagate **exit code** to **`spawn`** (**`os.wait`** / **`poll()`**); on **stdin EOF** close child **stdin** to allow clean shutdown (**SIGPIPE**/EOF depends on MCP server).

Signals (**optional note**): **SIGINT**/IDE stop may terminate **`spawn`** first — implementation should avoid leaking zombie children (**context manager** **`Popen`** or kill on interpreter exit handler if needed — **tests** sanity only).

#### IDE MCP **`command`** string
- **`"spawn"`** only: matches **`pyproject.toml`** **`[project.scripts]`** entry **`spawn = "spawn_cli.cli:main"`**. Do **not** render **`python -m`** forms; PATH setup is identical to invoking **`spawn`** manually from a repo shell.

#### Shared wrapper **`args`** list
- **`spawn_cli.ide.mcp_stdio_argv(extension_id: str, server_name: str) -> list[str]`** returning **`["mcp_stdio","extension",extension_id,"name",server_name]`** (**single importer for all MCP adapters**).
- **`add_mcp`** paths import this helper (**DRY**) for **`args`** substitution.

#### Adapters touched (**stdio** MCP emitters; confirm in tree)
- **`spawn_cli.ide.cursor`**, **`claude_code`**, **`gemini_cli`**, **`github_copilot`**, **`codex`** — each **`_build_*` / TOML** branch for **`transport.type == "stdio"`** gains **proxy fork**: **same structure as non-proxy** except **`command`/`args`**. **`windsurf`**: MCP unsupported today — **skip**.

#### Regression tests (**see also** **`4-tests-validation.md`**)
- Unit: JSON flag round-trip; **`extension_check`** bad combos.
- **CLI**: parser accepts exactly **`spawn mcp_stdio extension E name N`** (**argv** fragmentation).
- **`_dispatch`** / lock: asserting **`mcp_stdio`** execution path never acquires **`spawn_lock`** (**mock**/spy on **`spawn_lock`** context manager).
- Adapter goldens: **`command`** **`spawn`**; **`args`** start with **`mcp_stdio`**; **`env`** and **`cwd`** match the non-proxy case (**difference limited to **`command`** and **`args`**).

### Open points closed for this spec
1. **`spawn_stdio_proxy`** is the authoring flag (**boolean**) on **`servers[]`**, default **`false`** (confirmed).
2. Binding defaults (document exceptions only in **`spec/design/ide-adapters.md`**, Step **7**): **`spawn`** discoverable via **`PATH`**; **`mcp_stdio`** skips **`spawn_lock`**; MCP byte forwarding without Unicode text-mode mangling; inner **`stderr`** inherits by default (**`Popen`** **`stderr=None`**).

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `_DONE_1-mcp-proxy-schema.md` → step `_DONE_2-mcpstdio-cli.md` → step `_DONE_3-mcp-render-adapters.md` → step `_DONE_4-tests-validation.md`
- Phase 2 (sequential): step review — inspect all changes, fix inconsistencies
