# 3: Smoke test

## Goal
Add a minimal automated check for the CLI entrypoint wiring.

## Approach
Create a pytest smoke test that calls the CLI with `--help`, expects a successful `SystemExit(0)` or return path consistent with `argparse`, and verifies help text contains the command identity.

## Affected files
- `tests/test_cli.py`

## Code examples
```python
def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
```
