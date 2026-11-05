---
name: spectask-execute-step-by-step-dual-review
description: Step 5 like spectask-execute-step-by-step, but every subtask is reviewed by TWO reviewer subagents of different models; spec deviations auto-fix, conceptual problems/spec bugs stop for a user decision (fix spec / spec+code / spec+revert).
---

**Mandatory:** read **spec/main.md** in full before acting — especially Steps 5–6, Coder protocol, Subagent run protocol.

**Role:** `A6-coordinator`

**User-tunable parameters (confirm once at start if not given):**

- coder model (executor `A5-coder`) — e.g. GLM-5.3
- reviewer models — exactly two, DIFFERENT model families (e.g. GLM-5.3-flash + Kimi-k3.1-pro)

**Rules:** `R7-process`, `R10-ask`, `R13-model-line`, `R14-changed-files`, `R15-done-marking`, `R16-ambient`

**Roles involved:** `A6-coordinator`, `A5-coder`, `A4-reviewer` (x2 per step, review-only), `A4-reviewer` (full Step 6)

## Per-subtask loop (repeat for each Execution Scheme subtask, in scheme order)

1. Launch ONE `A5-coder` subagent (coder model) for the subtask (Subagent run protocol, Coder protocol, `R13-model-line`); coder builds the solution (`dotnet build` or repo-equivalent) and lists changed files (`R14`).
2. Mark done per `R15-done-marking` (rename to `_DONE_{N}`, set `Used model`).
3. Launch TWO `A4-reviewer` subagents IN PARALLEL (the two reviewer models), same ambient rules. Both are REVIEW-ONLY: they must not edit files. Ask each for a verdict:
   - `OK` — no findings
   - `SPEC_DEVIATIONS` — implementation diverges from the spec (wrong/missing symbols, changed behavior)
   - `CONCEPTUAL_PROBLEM` — spec bug, impossible contract, design flaw, cross-step breakage
4. Triage findings:
   - both `OK` -> next subtask.
   - `SPEC_DEVIATIONS` (or minor leftover text inconsistencies) -> do NOT stop: fix directly (coordinator or relaunch the coder with the findings), optionally a quick re-check by the stricter reviewer, then next subtask.
   - `CONCEPTUAL_PROBLEM` -> STOP. Present findings to the user with your assessment (which are credible, recommended fixes) and ask (`R10-ask`) to choose:
     a) fix spec only (code aligned later / in next steps)
     b) fix spec + fix code now
     c) fix spec + re-run review of the fixes, then REVERT all implemented code and set every executed subtask back to undone (Status: Not implemented, empty Used model, rename from `_DONE_`) for a fresh re-run
     d) user handles it
5. Record every accepted fix round in the task's review-findings file and overview `## Details` (numbered rounds: what was found, what was decided, what changed).

## Completion

- When all subtasks done: mark `Code implementation [model]`, run full **Step 6** (`A4-reviewer` over all changes) per **spec/main.md**, then stop and wait for user Step 7.
- Escalation rule stays active during Step 6: deviations auto-fix, conceptual problems stop for a user decision.

## Notes

- Reviewer prompts must state: authoritative spec files, the implemented file list, round-specific fixes to verify, verdict format, and `My model:` line (`R13`).
- When a coder must deviate for compilation (e.g. aligning earlier-step code with a just-fixed spec), instruct it to keep edits MINIMAL and report them separately as "alignment edits".
