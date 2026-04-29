# 0: Initialize Python CLI project

IMPORTANT: always use `spec/main.md` and `spec/navigation.yaml` for rules.

## Status
- [V] Spec created
- [V] Self spec review passed
- [V] Spec review passed
- [V] Code implemented
- [V] Self code review passed
- [V] Code review passed
- [V] HLA updated

## Goal
Initialize this repository as a minimal installable Python CLI project.

## Design overview
- Affected modules: project metadata, Python package source tree, CLI entrypoint, tests.
- Data flow changes: command-line arguments enter through the console script, route into the package CLI module, and produce process output plus an exit code.
- Integration points: Python packaging via `pyproject.toml`, console script named `spawn`, and pytest-based smoke tests.

## Before -> After
### Before
- The repository contains only spec/process files and no Python package, CLI entrypoint, or test scaffold.
- The example task `spec/tasks/0-example-hello` exists only as placeholder documentation.
### After
- The example task is removed from active specs.
- The repository has a `src/` layout Python package with a minimal CLI module.
- The project can be installed as a package exposing a `spawn` console command.
- A basic test verifies that the CLI help path is wired correctly.

## Details
Implementation clarifications and agreed defaults:
- Use `pyproject.toml` as the single project metadata and build configuration file.
- Use `setuptools` with a `src/` layout to keep packaging simple and dependency-light.
- Use the standard library `argparse` for the first CLI surface; do not add Typer or Click yet.
- Use package name `spawn_cli` and console script name `spawn`.
- Target Python `>=3.11` unless local constraints discovered during implementation require a narrower or wider version.
- Add `pytest` configuration and a minimal smoke test, but do not add broad application behavior yet.
- Keep user-facing CLI text in English.

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions - even if a step seems trivial or small.
- Phase 1 (sequential): step `1-project-metadata` -> step `2-cli-package` -> step `3-smoke-test`
- Phase 2 (sequential): step review - inspect all changes, fix inconsistencies
