# 21: Interactive extension setup hook subprocesses

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
Run extension setup hook subprocesses with inherited standard I/O so terminal users see live script output and can respond to interactive prompts.

## Design overview
- Affected modules: `spawn_cli.core.scripts` (`_run_script`, `run_after_uninstall_from_snapshot`, `run_healthcheck_scripts`); tests under `tests/core/test_scripts.py`.
- Data flow changes: subprocess invocations stop capturing stdout/stderr; stdin remains inherited. Failure handling no longer appends captured stderr from `CompletedProcess` (the user already saw the stream); messages still include script identity and exit code.
- Integration points: unchanged call sites in `spawn_cli.core.high_level` and download/refresh flows; environment variables and `cwd` contract stay the same.

## Before -> After
### Before
- Setup hooks and healthcheck use `subprocess.run(..., capture_output=True, text=True)`, so child stdout/stderr are buffered inside the parent hook until the script exits, and the child does not read the user's terminal stdin.
### After
- Those subprocesses use the default inherited stdin/stdout/stderr (equivalent to explicit `sys.stdin` / `sys.stdout` / `sys.stderr`), so output and prompts appear in real time and interactive scripts work when the user runs Spawn in a normal terminal.

## Details
- **Scope**: Apply to every setup-script runner implemented in `scripts.py`: all phases configured under `config.yaml` `setup` (`before-install`, `after-install`, `before-uninstall`, `after-uninstall`), `run_after_uninstall_from_snapshot`, and `run_healthcheck_scripts`. One consistent behavior avoids surprising differences between install and other phases.
- **Blocking vs warning**: Unchanged: non-zero exit still raises `SpawnError` for blocking phases or emits `SpawnWarning` for non-blocking phases; only the construction of the human-readable message drops reliance on `proc.stderr` content (optional one-line hint that stderr was already printed).
- **Tests**: Replace or adjust assertions that depended on `capture_output` (e.g. patch `subprocess.run` and assert `capture_output` is false or absent). Add a focused test that the child can read stdin when driving the hook (e.g. script reads a line and exits 0; parent thread writes to `sys.stdin` or use a small integration pattern with `subprocess` mock that checks `stdin` inheritance) if straightforward; otherwise document manual verification for interactive behavior.
- **Documentation**: Step 7 updates `spec/design/hla.md` (scripts bullet), `spec/design/utility.md`, and `spec/design/utility-method-flows.md` setup-scripts section to state that hook subprocesses inherit the parent standard streams and progress line remains on stderr before launch.

## Implementation notes
- **`subprocess.run`**: In `_run_script`, `run_after_uninstall_from_snapshot`, and `run_healthcheck_scripts`, remove `capture_output=True` and `text=True`. Do not set `stdin`, `stdout`, or `stderr` so the child inherits the Spawn process streams (same as the user terminal when Spawn is run interactively).
- **`CompletedProcess`**: With no capture, `stdout` and `stderr` on the result are `None`; callers of `_run_script` today only use `returncode` indirectly via the error path, so no API change for external modules.
- **Failure messages**: Drop the branch that appends `proc.stderr.strip()` to `SpawnError` / warning text (stderr was already printed). Keep script id (e.g. `script_filename` or snapshot basename) and exit code; optional short suffix such as `"(output above)"` if that improves clarity without being noisy.
- **Progress line**: Keep the existing `print(..., file=sys.stderr)` immediately before each `subprocess.run`; it must remain the line users rely on to see which phase started.
- **Environment and argv**: Unchanged: `[sys.executable, str(script_path)]`, `cwd=str(target_root.resolve())`, env block with `SPAWN_*` keys as today (`run_healthcheck_scripts` may keep its dict-literal merge pattern).
- **Refactor (optional)**: If three `subprocess.run` blocks become duplicated after edits, factor a small private helper (e.g. run hook with inherited stdio) in the same module; otherwise leave inline for minimal diff.
- **`test_scripts.py`**: Extend `test_env_vars_passed` (or equivalent) so the patched `subprocess.run` call does not pass `capture_output=True`. Add `assert run.call_args.kwargs.get("capture_output") is not True` or `assert "capture_output" not in run.call_args.kwargs`. Existing success/failure tests stay valid if the mock still returns a `CompletedProcess` with `returncode` set; use `stdout=None`, `stderr=None` on the fake object to match real behavior. Optionally add one test that documents expected kwargs: no `stdin`/`stdout`/`stderr` overrides unless a future feature requires them.
- **No change**: `SCRIPT_ENV_VARS`, snapshot copy logic, public function signatures, and call sites in `high_level` / download remain as-is unless a follow-up task needs them.
