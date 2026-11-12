linked task: none

Cline ignore is deprecated and ineffective as an access boundary — replace adapter agent-ignore mechanism with Hooks guard (or spawn-level rules).

Facts (verified via sources below):
- .clineignore only filters what Cline auto-loads into context; it is NOT a security/access boundary, and the agent can bypass it (e.g. via shell). Deprecated: docs say "will be deprecated soon", deprecations page lists it without direct replacement.
- Actual mechanism since Cline 3.36 (Nov 2025): Hooks. PreToolUse hook receives JSON on stdin (tool name, params, workspaceRoots) and returns {"cancel": true, "errorMessage": "..."} or {"cancel": false}. Locations: project .clinerules/hooks/PreToolUse (VS Code ext, no extension) or .cline/hooks/PreToolUse.sh (CLI/SDK); global ~/Documents/Cline/Rules/Hooks/. Must enable "Enable Hooks" in settings.
- Official example sdk/examples/hooks/PreToolUse_ClineignoreGuard.sh re-implements .clineignore via hooks: intercepts read_files, editor, apply_patch, run_commands, normalizes paths, matches via git check-ignore; also guards .clineignore itself from agent edits.
- LIMITATION: hooks are macOS/Linux only; NO Windows support. On win32 (e.g. this user's env) the hook guard does not work and .clineignore context filtering is not applied by Cline — tools still see ignored files.

Spawn implications (candidate task):
- Current ClineAdapter agent_ignore=native via .clineignore is weak on Windows / being deprecated upstream.
- Options to evaluate: emit capability warning for cline agent-ignore (weak enforcement); optional PreToolUse hook installer (non-Windows only); or rely on spawn-level rules (navigation.yaml read-required scoping / "do not read" rules) and physical archiving of _DONE_* task folders outside the working tree.
- Do not remove .clineignore support yet (still functional for context filtering); consider detect() also checking .cline/hooks.

Sources:
- https://docs.cline.bot/customization/clineignore
- https://docs.cline.bot/resources/deprecations
- https://cline.ghost.io/cline-v3-36-hooks
- https://github.com/cline/cline/blob/main/sdk/examples/hooks/PreToolUse_ClineignoreGuard.sh
- https://fast.io/resources/cline-clineignore-guide
- https://www.reddit.com/r/CLine/comments/1v3jhyg/were_deprecating_clineignore_heres_what_to_use
