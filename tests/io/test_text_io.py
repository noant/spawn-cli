from __future__ import annotations

from spawn_cli.io import text_io


def test_read_lines_missing_returns_empty(tmp_path) -> None:
    assert text_io.read_lines(tmp_path / "absent.txt") == []


def test_write_then_read_lines(tmp_path) -> None:
    p = tmp_path / "t.txt"
    text_io.write_lines(p, ["a", "b", "c"])
    assert text_io.read_lines(p) == ["a", "b", "c"]


def test_write_lines_empty_file(tmp_path) -> None:
    p = tmp_path / "e.txt"
    text_io.write_lines(p, [])
    assert p.read_text(encoding="utf-8") == ""


def test_write_lines_trailing_newline_when_nonempty(tmp_path) -> None:
    p = tmp_path / "x.txt"
    text_io.write_lines(p, ["one"])
    assert p.read_bytes().endswith(b"\n")
