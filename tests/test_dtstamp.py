# tests/test_dtstamp.py
"""RFC 5545 §3.6.1: every VEVENT carries exactly one DTSTAMP (a fixed value, so output stays deterministic)."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from calmoji.cli import main
from calmoji.constants import DTSTAMP
from calmoji.ics_writer import unfold_ics_lines
from calmoji.types import Event

UTC = datetime.timezone.utc


def test_dtstamp_is_the_fixed_constant():
    assert DTSTAMP == "20260101T000000Z"


def test_dtstamp_follows_uid_in_timed_and_all_day_events():
    start = datetime.datetime(2027, 3, 1, 9, 5, tzinfo=UTC)
    for event in (Event(start=start, summary="timed"), Event(start=start, summary="all day", all_day=True)):
        lines = event.to_ics()
        assert lines[1].startswith("UID:")
        assert lines[2] == f"DTSTAMP:{DTSTAMP}"
        assert sum(1 for line in lines if line.startswith("DTSTAMP")) == 1


def _vevents(path: Path):
    events, current = [], None
    for line in unfold_ics_lines(path.read_text(encoding="utf-8")):
        if line == "BEGIN:VEVENT":
            current = []
        elif line == "END:VEVENT":
            events.append(current)
            current = None
        elif current is not None:
            current.append(line)
    return events


@pytest.mark.parametrize("alignment", ["academic", "calendar"])
def test_every_vevent_in_every_generated_file_has_exactly_one_dtstamp(tmp_path, alignment):
    main(["--year=2027", f"--calendar-alignment={alignment}", f"--output-dir={tmp_path}", "--include-oceania"])

    files = sorted(tmp_path.rglob("*.ics"))
    assert files
    checked = 0
    for path in files:
        for lines in _vevents(path):
            stamps = [line for line in lines if line.startswith("DTSTAMP")]
            assert stamps == [f"DTSTAMP:{DTSTAMP}"], f"{path.name}: {stamps}"
            checked += 1
    assert checked > 1000
