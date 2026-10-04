# tests/test_budget.py
"""The size budget: no .ics file calmoji writes may exceed MAX_EVENTS_PER_FILE or MAX_BYTES_PER_FILE."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from calmoji.calendar_config import ALIGNMENT_MODES
from calmoji.cli import main
from calmoji.constants import MAX_BYTES_PER_FILE, MAX_EVENTS_PER_FILE
from calmoji.ics_writer import IcsBudgetError, write_events_to_ics
from calmoji.types import Event

UTC = datetime.timezone.utc
START = datetime.datetime(2027, 1, 1, tzinfo=UTC)


def events(n: int, description: str = "") -> list:
    return [
        Event(start=START + datetime.timedelta(minutes=i), summary=f"event {i}", description=description)
        for i in range(n)
    ]


def test_the_budget_is_defined_once_with_the_agreed_numbers():
    assert MAX_EVENTS_PER_FILE == 600
    assert MAX_BYTES_PER_FILE == 512 * 1024


def test_a_file_at_the_event_limit_is_written(tmp_path):
    write_events_to_ics(events(MAX_EVENTS_PER_FILE), tmp_path / "ok.ics")
    assert (tmp_path / "ok.ics").stat().st_size <= MAX_BYTES_PER_FILE


def test_one_event_over_the_limit_raises_and_writes_nothing(tmp_path):
    with pytest.raises(IcsBudgetError, match=r"601 events.*600"):
        write_events_to_ics(events(MAX_EVENTS_PER_FILE + 1), tmp_path / "sub" / "big.ics")
    assert not (tmp_path / "sub").exists()


def test_a_file_over_the_byte_limit_raises_and_writes_nothing(tmp_path):
    padded = events(400, description="x" * 1500)  # few events, but each is large
    with pytest.raises(IcsBudgetError, match=r"bytes.*524,288"):
        write_events_to_ics(padded, tmp_path / "heavy.ics")
    assert not (tmp_path / "heavy.ics").exists()


def test_the_byte_limit_is_exact(tmp_path, monkeypatch):
    write_events_to_ics(events(3), tmp_path / "probe.ics")
    size = (tmp_path / "probe.ics").stat().st_size

    monkeypatch.setattr("calmoji.ics_writer.MAX_BYTES_PER_FILE", size)
    write_events_to_ics(events(3), tmp_path / "exactly.ics")  # exactly at the limit: allowed

    monkeypatch.setattr("calmoji.ics_writer.MAX_BYTES_PER_FILE", size - 1)
    with pytest.raises(IcsBudgetError):
        write_events_to_ics(events(3), tmp_path / "one_byte_over.ics")


def test_the_budget_error_is_a_value_error():
    assert issubclass(IcsBudgetError, ValueError)


def count_events(path: Path) -> int:
    return path.read_bytes().count(b"\nBEGIN:VEVENT\r\n")


def test_every_file_of_every_alignment_and_year_is_within_budget(tmp_path):
    """
    Every alignment x every year 2026-2039, with --include-oceania (the most events
    any meeting file can hold), through the real CLI. Also records the largest files.
    """
    files = 0
    largest_events = (0, "")
    largest_bytes = (0, "")

    for alignment in sorted(ALIGNMENT_MODES):
        for year in range(2026, 2040):
            outdir = tmp_path / alignment / str(year)
            main([f"--year={year}", f"--calendar-alignment={alignment}", f"--output-dir={outdir}", "--include-oceania"])
            for path in outdir.rglob("*.ics"):
                files += 1
                n_events, n_bytes = count_events(path), path.stat().st_size
                assert n_events <= MAX_EVENTS_PER_FILE, f"{path}: {n_events} events"
                assert n_bytes <= MAX_BYTES_PER_FILE, f"{path}: {n_bytes} bytes"
                largest_events = max(largest_events, (n_events, str(path.relative_to(tmp_path))))
                largest_bytes = max(largest_bytes, (n_bytes, str(path.relative_to(tmp_path))))

    assert files > 2000
    # There is real headroom, not a file that just squeaks under.
    assert largest_events[0] <= MAX_EVENTS_PER_FILE * 0.75, largest_events
    assert largest_bytes[0] <= MAX_BYTES_PER_FILE * 0.5, largest_bytes
