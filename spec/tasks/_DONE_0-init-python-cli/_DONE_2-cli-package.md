# 2: CLI package

## Goal
Add the initial Python package and command-line entrypoint.

## Approach
Create `src/spawn_cli/` with package initialization and a small `cli.py` module using `argparse`. The entrypoint should expose `main(argv: list[str] | None = None) -> int` and be safe to call from tests.

## Affected files
- `src/spawn_cli/__init__.py`
- `src/spawn_cli/cli.py`

## Code examples
```python
def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return 0
```
