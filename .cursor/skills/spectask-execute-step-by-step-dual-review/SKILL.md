---
name: spectask-execute-step-by-step-dual-review
description: Step 5 — one subtask per run, each reviewed by two reviewer subagents of different models; deviations auto-fix, conceptual problems/spec bugs stop for a user decision (fix spec / spec+code / spec+revert).
---


Interactive cross-review variant of **spectask-execute-step-by-step**. Reviewer pairs come from the **Code review scheme** in `## Review models` (`R23-review-scheme`, chosen in Step 1.1) — do not re-ask them. In `[auto]` run mode use **spectask-execute** instead.

**Mandatory:** read **spec/main.md** in full — Steps 5-6, Coder protocol, Subagent run protocol.

**Role:** `A6-coordinator`

**Rules:** `R7-process`, `R10-ask`, `R13-model-line`, `R14-changed-files`, `R15-done-marking`, `R16-ambient`, `R23-review-scheme`

**Roles involved:** `A6-coordinator`, `A5-coder`, `A4-reviewer` (x2 per step, review-only), `A4-reviewer` (full Step 6)

**Per-subtask loop (each Execution Scheme subtask, in scheme order):**

1. Launch ONE `A5-coder` subagent for the subtask (Subagent run protocol, Coder protocol, `R13`); coder builds and lists changed files (`R14`).
2. Mark done per `R15-done-marking` (rename `_DONE_{N}`, set `Used model`).
3. Launch TWO `A4-reviewer` subagents IN PARALLEL (the cross-review model pair), same ambient rules. REVIEW-ONLY: they must not edit files. Each returns a verdict: `OK` / `SPEC_DEVIATIONS` (diverges from spec: wrong/missing symbols, changed behavior) / `CONCEPTUAL_PROBLEM` (spec bug, impossible contract, design flaw, cross-step breakage).
4. Triage:
   - both `OK` → next subtask.
   - `SPEC_DEVIATIONS` or minor text inconsistencies → do NOT stop: fix directly (coordinator or relaunch coder with findings), optional quick re-check by the stricter reviewer, next subtask.
   - `CONCEPTUAL_PROBLEM` → STOP. Present findings with your assessment; ask (`R10-ask`): a) fix spec only; b) fix spec + code now; c) fix spec + re-review, then REVERT all implemented code and reset executed subtasks (Status: Not implemented, empty `Used model`, rename from `_DONE_`) for a fresh re-run; d) user handles it.
5. Record accepted fix rounds in the review-findings file and overview `## Details` (numbered rounds: found / decided / changed).

**Completion:** all subtasks done → mark `Code implementation [model]`, run full **Step 6** per spec/main.md, then `[interactive]` wait for user Step 7 / `[auto]` continue to Step 8. Escalation rule stays active during Step 6.

**Notes:**
- Reviewer prompts must state: authoritative spec files, implemented file list, round-specific fixes to verify, verdict format, `My model:` line (`R13`).
- When a coder must deviate for compilation (e.g. aligning earlier-step code with a just-fixed spec), instruct MINIMAL edits reported separately as "alignment edits".


Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.
- Use the platform ask tool when available (R10-ask in spec/main.md); otherwise, stop and request input from the user.

Mandatory reads:
- `spec/main.md` - Spec-Tasks methodology — folder structure, eight-step process, overview template.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/rules/01-vacancy-cleanup-subtrees.md` - finalize_*_repo cleanup must know every adapter-written config subtree; avoid dead configs.
- `spawn/rules/02-agent-config-namespacing.md` - Local rule file.
- `spawn/rules/03-adapter-spawn-warning.md` - IDE adapters emit warnings via SpawnWarning category for friendly CLI output.
- `spawn/rules/04-adapter-skill-name-constraints.md` - Local rule file.
- `spawn/rules/05-adapter-canonical-config-file.md` - Local rule file.
- `spawn/rules/06-new-ide-adapter-checklist.md` - Local rule file.
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spec/design/hla.md` - Project high-level architecture; updated in Step 8.
