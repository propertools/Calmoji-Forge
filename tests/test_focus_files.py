# tests/test_focus_files.py
"""
End-to-end checks on the focus-block files the CLI writes.

Focus blocks are written like meeting slots: one file per phase, clipped to the
phase's dates, plus one consolidated file per year. These tests generate real
files through the CLI and read them back, for both common alignments and for
consecutive years that include leap years (2027 spans 29 Feb 2028 in
`academic`; 2028 is itself a leap year in `calendar`).
"""

from __future__ import annotations

import datetime
from collections import Counter
from pathlib import Path
from typing import Dict, List

import pytest

from calmoji.calendar_phases import get_semester_phases
from calmoji.cli import main
from calmoji.focus_blocks_config import FOCUS_BLOCKS
from calmoji.ics_writer import unfold_ics_lines
from calmoji.utils import format_range_slug, slugify

UTC = datetime.timezone.utc

ALIGNMENTS = ["academic", "calendar"]
YEARS = [2026, 2027, 2028, 2029]
BLOCKS_PER_DAY = len(FOCUS_BLOCKS)

Ics = Dict[str, str]


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def read_events(path: Path) -> List[Ics]:
    """Parse the VEVENTs of an .ics file into dicts (property name -> value)."""
    events: List[Ics] = []
    current = None
    for line in unfold_ics_lines(path.read_text(encoding="utf-8")):
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT":
            assert current is not None
            events.append(current)
            current = None
        elif current is not None:
            name, _, value = line.partition(":")
            current[name] = value
    return events


def is_all_day(event: Ics) -> bool:
    return "DTSTART;VALUE=DATE" in event


def start_of(event: Ics) -> datetime.datetime:
    if is_all_day(event):
        return datetime.datetime.strptime(event["DTSTART;VALUE=DATE"], "%Y%m%d").replace(tzinfo=UTC)
    return datetime.datetime.strptime(event["DTSTART"], "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)


def phase_files(outdir: Path, year: int, alignment: str):
    """Yield (phase, path) for every phase of the year, using the documented file name."""
    for phase in get_semester_phases(year, alignment):
        assert phase.start is not None and phase.end is not None
        name = f"focus_{slugify(phase.name)}_{format_range_slug(phase.start, phase.end)}.ics"
        yield phase, outdir / name


@pytest.fixture(scope="module")
def outputs(tmp_path_factory: pytest.TempPathFactory) -> Dict[tuple, Path]:
    """Run the CLI once per (alignment, year); focus blocks only, to keep it quick."""
    result: Dict[tuple, Path] = {}
    for alignment in ALIGNMENTS:
        for year in YEARS:
            outdir = tmp_path_factory.mktemp(f"{alignment}-{year}")
            main(
                [
                    f"--year={year}",
                    f"--calendar-alignment={alignment}",
                    f"--output-dir={outdir}",
                    "--no-meetings",
                    "--no-ebi48",
                ]
            )
            result[(alignment, year)] = outdir
    return result


# -----------------------------------------------------------------------------
# Layout
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("alignment", ALIGNMENTS)
@pytest.mark.parametrize("year", YEARS)
def test_layout_is_one_file_per_phase_plus_one_per_year(outputs, alignment, year):
    outdir = outputs[(alignment, year)]

    assert not (outdir / "focus_weeks").exists(), "weekly focus files are gone"

    expected = {path.name for _, path in phase_files(outdir, year, alignment)} | {f"focus_all_{year}.ics"}
    actual = {p.name for p in outdir.glob("focus_*")}
    assert actual == expected


# -----------------------------------------------------------------------------
# No duplicates
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("alignment", ALIGNMENTS)
@pytest.mark.parametrize("year", YEARS)
def test_no_focus_block_start_time_appears_twice_within_a_year(outputs, alignment, year):
    outdir = outputs[(alignment, year)]

    for source in [outdir / f"focus_all_{year}.ics"] + [path for _, path in phase_files(outdir, year, alignment)]:
        events = read_events(source)
        block_starts = [start_of(e) for e in events if not is_all_day(e)]
        key_starts = [start_of(e) for e in events if is_all_day(e)]
        assert len(block_starts) == len(set(block_starts)), f"duplicate focus-block start in {source.name}"
        assert len(key_starts) == len(set(key_starts)), f"duplicate Glyph Key in {source.name}"

    # ...and across the per-phase files taken together.
    per_phase_starts = [
        start_of(e) for _, path in phase_files(outdir, year, alignment) for e in read_events(path) if not is_all_day(e)
    ]
    assert len(per_phase_starts) == len(set(per_phase_starts))


@pytest.mark.parametrize("alignment", ALIGNMENTS)
@pytest.mark.parametrize("year", YEARS)
def test_uids_are_unique_within_a_year(outputs, alignment, year):
    uids = [e["UID"] for e in read_events(outputs[(alignment, year)] / f"focus_all_{year}.ics")]
    assert len(uids) == len(set(uids))


# -----------------------------------------------------------------------------
# Clipping
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("alignment", ALIGNMENTS)
@pytest.mark.parametrize("year", YEARS)
def test_every_event_in_a_phase_file_starts_within_that_phase(outputs, alignment, year):
    outdir = outputs[(alignment, year)]

    for phase, path in phase_files(outdir, year, alignment):
        assert path.exists(), f"missing {path.name}"
        events = read_events(path)
        assert events, f"{path.name} is empty"
        assert phase.start is not None and phase.end is not None
        outside = [e["DTSTART"] for e in events if not phase.start <= start_of(e) < phase.end]
        assert not outside, f"{path.name} has events outside {phase.start} .. {phase.end}: {outside[:3]}"


@pytest.mark.parametrize("alignment", ALIGNMENTS)
@pytest.mark.parametrize("year", YEARS)
def test_each_day_of_each_phase_has_a_full_set_of_blocks(outputs, alignment, year):
    outdir = outputs[(alignment, year)]

    for phase, path in phase_files(outdir, year, alignment):
        assert phase.start is not None and phase.end is not None
        per_day = Counter(start_of(e).date() for e in read_events(path) if not is_all_day(e))
        days = [phase.start.date() + datetime.timedelta(days=i) for i in range((phase.end - phase.start).days)]
        assert sorted(per_day) == days
        assert set(per_day.values()) == {BLOCKS_PER_DAY}


# -----------------------------------------------------------------------------
# Consolidated file
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("alignment", ALIGNMENTS)
@pytest.mark.parametrize("year", YEARS)
def test_focus_all_is_the_union_of_the_phase_files(outputs, alignment, year):
    outdir = outputs[(alignment, year)]

    union = [e for _, path in phase_files(outdir, year, alignment) for e in read_events(path)]
    consolidated = read_events(outdir / f"focus_all_{year}.ics")

    assert len(consolidated) == len(union)
    assert Counter(e["UID"] for e in consolidated) == Counter(e["UID"] for e in union)
    assert sorted(consolidated, key=lambda e: sorted(e.items())) == sorted(union, key=lambda e: sorted(e.items()))
    assert [start_of(e) for e in consolidated] == sorted(start_of(e) for e in consolidated)


# -----------------------------------------------------------------------------
# Counts
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("alignment", ALIGNMENTS)
@pytest.mark.parametrize("year", YEARS)
def test_focus_block_count_per_year(outputs, alignment, year):
    # Default 7-day week: every day of the year's phases gets a full set of blocks,
    # plus one Glyph Key on each Monday in range.
    phases = get_semester_phases(year, alignment)
    first, last = phases[0].start, phases[-1].end
    assert first is not None and last is not None
    days_in_phases = sum((p.end - p.start).days for p in phases if p.start and p.end)
    mondays = sum(1 for i in range((last - first).days) if (first + datetime.timedelta(days=i)).weekday() == 0)

    events = read_events(outputs[(alignment, year)] / f"focus_all_{year}.ics")

    assert sum(1 for e in events if not is_all_day(e)) == BLOCKS_PER_DAY * days_in_phases
    assert sum(1 for e in events if is_all_day(e)) == mondays
    assert len(events) == BLOCKS_PER_DAY * days_in_phases + mondays


# -----------------------------------------------------------------------------
# Consecutive years
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("alignment", ALIGNMENTS)
@pytest.mark.parametrize("year", YEARS[:-1])
def test_consecutive_years_share_no_focus_block_start_times(outputs, alignment, year):
    this_year = read_events(outputs[(alignment, year)] / f"focus_all_{year}.ics")
    next_year = read_events(outputs[(alignment, year + 1)] / f"focus_all_{year + 1}.ics")

    assert {start_of(e) for e in this_year if not is_all_day(e)}.isdisjoint(
        {start_of(e) for e in next_year if not is_all_day(e)}
    )
    assert {start_of(e) for e in this_year if is_all_day(e)}.isdisjoint(
        {start_of(e) for e in next_year if is_all_day(e)}
    )
    assert {e["UID"] for e in this_year}.isdisjoint({e["UID"] for e in next_year})


# -----------------------------------------------------------------------------
# CLI switches
# -----------------------------------------------------------------------------


def test_dry_run_previews_focus_blocks_per_phase_and_writes_nothing(tmp_path, capsys):
    outdir = tmp_path / "out"

    main(["--year=2027", f"--output-dir={outdir}", "--dry-run"])

    shown = capsys.readouterr().out
    phases = get_semester_phases(2027, "academic")
    assert shown.count("focus blocks\n") == len(phases)  # one "Total: N focus blocks" line per phase
    for phase in phases:
        assert phase.start is not None and phase.end is not None
        days = [phase.start + datetime.timedelta(days=i) for i in range((phase.end - phase.start).days)]
        expected = BLOCKS_PER_DAY * len(days) + sum(1 for d in days if d.weekday() == 0)
        assert f"📆 {phase.name}\n" in shown
        assert f"Total: {expected} focus blocks\n" in shown
    assert "Focus Block 1 — Semester A (Seed)" in shown
    assert not outdir.exists(), "dry-run must not write files"


def test_no_focus_flag_skips_focus_files(tmp_path):
    main(["--year=2027", f"--output-dir={tmp_path}", "--no-focus", "--no-meetings", "--no-ebi48"])

    assert not list(tmp_path.glob("focus_*"))
    assert (tmp_path / "semester_phases_2027.ics").exists()
