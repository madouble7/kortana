from __future__ import annotations

from pathlib import Path

from relays.protocol import append_text_line, tail_text_lines


def test_append_text_line_always_terminates_with_newline(tmp_path: Path) -> None:
    path = tmp_path / "events.log"
    append_text_line(path, "first")
    append_text_line(path, "second\n")

    content = path.read_text(encoding="utf-8")
    assert content == "first\nsecond\n"


def test_tail_text_lines_buffers_incomplete_line(tmp_path: Path) -> None:
    path = tmp_path / "queue.txt"
    path.write_text("one\npartial", encoding="utf-8")

    lines, offset, remainder = tail_text_lines(path, offset=0, remainder="")
    assert lines == ["one"]
    assert remainder == "partial"

    with open(path, "a", encoding="utf-8") as f:
        f.write("_done\n")

    lines2, offset2, remainder2 = tail_text_lines(
        path,
        offset=offset,
        remainder=remainder,
    )
    assert lines2 == ["partial_done"]
    assert remainder2 == ""
    assert offset2 >= offset
