# tests/test_monthly_files.py
"""
End-to-end checks on the monthly files the CLI writes.

Focus blocks and meeting slots are written one file per UTC month under focus/ and
meetings/. These tests generate real files through the CLI and read them back, for
the two common alignments over consecutive years that include leap years (2027
academic spans 29 Feb 2028; 2028 calendar is itself a leap year), and for the two
placeholder alignments whose years start mid-month.
"""

from __future__ import annotations

import datetime
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

from calmoji.calendar_config import get_year_start_date
from calmoji.calendar_phases import get_semester_phases
from calmoji.cli import main
from calmoji.constants import CALNAME_FOCUS, CALNAME_MEETINGS, OUTPUT_MARKER_NAME
from calmoji.focus_blocks_config import FOCUS_BLOCKS
from calmoji.meeting_slots import MEETING_SLOTS
from tests.ics_helpers import Ics, header_lines, is_all_day, read_events, start_of

UTC = datetime.timezone.utc
DAY = datetime.timedelta(days=1)

ALIGNMENTS = ["academic", "calendar"]
MARKER = OUTPUT_MARKER_NAME
YEARS = [2026, 2027, 2028, 2029]
BLOCKS_PER_DAY = len(FOCUS_BLOCKS)
MONTH_FILE_RE = re.compile(r"^(focus|meetings)_(\d{4})-(\d{2})\.ics$")

Outputs = Dict[Tuple[str, int], Path]


def run_cli(outdir: Path, year: int, alignment: str, *extra: str) -> None:
    main([f"--year={year}", f"--calendar-alignment={alignment}", f"--output-dir={outdir}", *extra])


@pytest.fixture(scope="module")
def outputs(tmp_path_factory: pytest.TempPathFactory) -> Outputs:
    """Run the CLI once per (alignment, year) with default options."""
    result: Outputs = {}
    for alignment in ["academic", "calendar", "chinese_lunar", "islamic_hijri"]:
        for year in YEARS:
            outdir = tmp_path_factory.mktemp(f"{alignment}-{year}")
            run_cli(outdir, year, alignment)
            result[(alignment, year)] = outdir
    return result


def months_of_year(year: int, alignment: str) -> List[str]:
    """Every UTC month touched by [anchor, next anchor), as 'YYYY-MM'."""
    first = get_year_start_date(year, alignment)
    last = get_year_start_date(year + 1, alignment) - DAY
    months, cur = [], (first.year, first.month)
    while cur <= (last.year, last.month):
        months.append(f"{cur[0]:04d}-{cur[1]:02d}")
        cur = (cur[0] + (cur[1] == 12), cur[1] % 12 + 1)
    return months


def months_with_meeting_days(year: int, alignment: str) -> List[str]:
    months = set()
    for phase in get_semester_phases(year, alignment):
        if phase.allow_meetings:
            months.update((phase.start + i * DAY).strftime("%Y-%m") for i in range((phase.end - phase.start).days))
    return sorted(months)


def month_files(outdir: Path, kind: str) -> Dict[str, Path]:
    files = {}
    for path in (outdir / kind).iterdir():
        match = MONTH_FILE_RE.match(path.name)
        assert match, path.name
        files[f"{match.group(2)}-{match.group(3)}"] = path
    return files


def all_events(outdir: Path, kind: str) -> List[Tuple[str, Ics]]:
    return [(month, e) for month, path in sorted(month_files(outdir, kind).items()) for e in read_events(path)]


# -----------------------------------------------------------------------------
# Layout
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("alignment", ["academic", "calendar", "chinese_lunar", "islamic_hijri"])
@pytest.mark.parametrize("year", YEARS)
def test_layout(outputs, alignment, year):
    outdir = outputs[(alignment, year)]
    top = sorted(p.name for p in outdir.iterdir())
    assert top == sorted([MARKER, f"emoji_clock_{year}.ics", "focus", "meetings", f"seasons_{year}.ics"])

    assert sorted(p.name for p in (outdir / "focus").iterdir()) == [
        f"focus_{m}.ics" for m in months_of_year(year, alignment)
    ]
    # Only months that have events get a file. Meeting slots run in some phases only, so a
    # partial edge month that falls wholly in a no-meetings phase has no meetings file.
    assert sorted(p.name for p in (outdir / "meetings").iterdir()) == [
        f"meetings_{m}.ics" for m in months_with_meeting_days(year, alignment)
    ]


@pytest.mark.parametrize("alignment", ["academic", "calendar"])
def test_the_retired_files_are_gone(outputs, alignment):
    outdir = outputs[(alignment, 2027)]
    names = {p.name for p in outdir.rglob("*") if p.is_file()}
    assert not any(n.startswith(("focus_all", "meeting_all", "meeting_")) for n in names)
    assert not any(n.startswith("focus_") and not MONTH_FILE_RE.match(n) for n in names)
    assert not (outdir / "focus_weeks").exists()


def test_the_2027_academic_tree(outputs):
    outdir = outputs[("academic", 2027)]
    tree = sorted(p.relative_to(outdir).as_posix() for p in outdir.rglob("*.ics"))
    assert tree[0] == "emoji_clock_2027.ics"
    assert "focus/focus_2027-09.ics" in tree and "focus/focus_2028-08.ics" in tree
    assert "meetings/meetings_2027-09.ics" in tree and "meetings/meetings_2028-08.ics" in tree
    assert tree[-1] == "seasons_2027.ics"
    assert len(tree) == 2 + 12 + 12


@pytest.mark.parametrize("alignment", ["academic", "calendar"])
def test_calendar_names_are_constant_per_layer(outputs, alignment):
    outdir = outputs[(alignment, 2028)]
    for path in (outdir / "focus").iterdir():
        assert f"X-WR-CALNAME:{CALNAME_FOCUS}" in header_lines(path)
    for path in (outdir / "meetings").iterdir():
        assert f"X-WR-CALNAME:{CALNAME_MEETINGS}" in header_lines(path)
    assert CALNAME_FOCUS == "🧠 Focus — Open"
    assert CALNAME_MEETINGS == "🕒 Meetings — Open"


# -----------------------------------------------------------------------------
# Bucketing: every event in exactly one file, the file of its UTC month
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("alignment", ["academic", "calendar", "chinese_lunar", "islamic_hijri"])
@pytest.mark.parametrize("year", YEARS)
@pytest.mark.parametrize("kind", ["focus", "meetings"])
def test_every_event_is_in_the_file_of_its_utc_month(outputs, alignment, year, kind):
    events = all_events(outputs[(alignment, year)], kind)
    assert events
    for month, event in events:
        assert start_of(event).strftime("%Y-%m") == month, f"{kind}_{month}: {event['SUMMARY']} {event.get('DTSTART')}"


@pytest.mark.parametrize("alignment", ["academic", "calendar", "chinese_lunar", "islamic_hijri"])
@pytest.mark.parametrize("year", YEARS[:-1])
def test_no_event_appears_in_two_files(outputs, alignment, year):
    # Within a year's folder, and across the folders of consecutive years (where a mid-month
    # anchor splits a month between two folders).
    uids: Counter = Counter()
    starts: Counter = Counter()
    for y in (year, year + 1):
        for kind in ("focus", "meetings"):
            for _, event in all_events(outputs[(alignment, y)], kind):
                uids[event["UID"]] += 1
                if kind == "focus" and not is_all_day(event):
                    starts[start_of(event)] += 1
    assert max(uids.values()) == 1
    assert max(starts.values()) == 1


@pytest.mark.parametrize("alignment", ["chinese_lunar", "islamic_hijri"])
def test_a_mid_month_anchor_splits_the_edge_month_between_two_folders(outputs, alignment):
    anchor = get_year_start_date(2028, alignment)
    assert anchor.day != 1
    month = anchor.strftime("%Y-%m")

    before = [e for _, e in all_events(outputs[(alignment, 2027)], "focus") if start_of(e).strftime("%Y-%m") == month]
    after = [e for _, e in all_events(outputs[(alignment, 2028)], "focus") if start_of(e).strftime("%Y-%m") == month]
    assert before and after
    assert max(start_of(e) for e in before) < anchor <= min(start_of(e) for e in after)

    # together they make the whole month
    month_days = {start_of(e).date() for e in before + after if not is_all_day(e)}
    first = anchor.replace(day=1)
    next_month = (first + datetime.timedelta(days=32)).replace(day=1)
    assert month_days == {(first + i * DAY).date() for i in range((next_month - first).days)}


def test_a_glyph_key_goes_by_its_date(outputs):
    # Monday 2027-11-01 is the first of the month: its Glyph Key belongs in focus_2027-11, not October.
    november = read_events(outputs[("academic", 2027)] / "focus" / "focus_2027-11.ics")
    october = read_events(outputs[("academic", 2027)] / "focus" / "focus_2027-10.ics")
    key_date = datetime.datetime(2027, 11, 1, tzinfo=UTC)
    assert key_date.weekday() == 0
    assert any(is_all_day(e) and start_of(e) == key_date for e in november)
    assert not any(is_all_day(e) and start_of(e) == key_date for e in october)


# -----------------------------------------------------------------------------
# Focus blocks: clipped to phases, a full set every day, no duplicates
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("alignment", ALIGNMENTS)
@pytest.mark.parametrize("year", YEARS)
def test_focus_blocks_cover_every_day_of_the_year_exactly_once(outputs, alignment, year):
    anchor = get_year_start_date(year, alignment)
    next_anchor = get_year_start_date(year + 1, alignment)
    days = [anchor + i * DAY for i in range((next_anchor - anchor).days)]

    events = [e for _, e in all_events(outputs[(alignment, year)], "focus")]
    blocks = [e for e in events if not is_all_day(e)]
    starts = [start_of(e) for e in blocks]
    assert len(starts) == len(set(starts)), "a focus-block start time appears twice"

    per_day = Counter(s.date() for s in starts)
    assert sorted(per_day) == [d.date() for d in days]
    assert set(per_day.values()) == {BLOCKS_PER_DAY}

    mondays = [d for d in days if d.weekday() == 0]
    keys = [start_of(e) for e in events if is_all_day(e)]
    assert sorted(keys) == mondays
    assert len(events) == BLOCKS_PER_DAY * len(days) + len(mondays)


@pytest.mark.parametrize("alignment", ALIGNMENTS)
@pytest.mark.parametrize("year", YEARS)
def test_each_focus_event_is_labelled_with_the_phase_it_falls_in(outputs, alignment, year):
    phases = get_semester_phases(year, alignment)
    for _, event in all_events(outputs[(alignment, year)], "focus"):
        start = start_of(event)
        (phase,) = [p for p in phases if p.start <= start < p.end]
        assert phase.name in event["SUMMARY"], event["SUMMARY"]


def test_the_leap_day_and_the_last_day_of_a_leap_spanning_year_are_in_the_files(outputs):
    feb = read_events(outputs[("academic", 2027)] / "focus" / "focus_2028-02.ics")
    assert sum(1 for e in feb if not is_all_day(e)) == 29 * BLOCKS_PER_DAY
    august = read_events(outputs[("academic", 2027)] / "focus" / "focus_2028-08.ics")
    assert max(start_of(e) for e in august).date() == datetime.date(2028, 8, 31)

    december = read_events(outputs[("calendar", 2028)] / "focus" / "focus_2028-12.ics")
    assert max(start_of(e) for e in december).date() == datetime.date(2028, 12, 31)


@pytest.mark.parametrize("alignment", ALIGNMENTS)
def test_consecutive_years_neither_overlap_nor_leave_a_gap(outputs, alignment):
    for year in YEARS[:-1]:
        last = max(start_of(e) for _, e in all_events(outputs[(alignment, year)], "focus"))
        first = min(start_of(e) for _, e in all_events(outputs[(alignment, year + 1)], "focus"))
        assert first.date() == last.date() + DAY, f"{alignment} {year} -> {year + 1}"
        assert first == get_year_start_date(year + 1, alignment)


# -----------------------------------------------------------------------------
# Meeting slots
# -----------------------------------------------------------------------------

WEEKDAYS = {"Mecca": {6, 0, 1, 2, 3}}
DEFAULT_WEEKDAYS = {0, 1, 2, 3, 4}


@pytest.mark.parametrize("alignment", ALIGNMENTS)
@pytest.mark.parametrize("year", YEARS)
def test_meeting_slots_are_exactly_the_slots_of_the_meeting_phases(outputs, alignment, year):
    expected = set()
    for phase in get_semester_phases(year, alignment):
        if not phase.allow_meetings:
            continue
        for i in range((phase.end - phase.start).days):
            day = phase.start + i * DAY
            for city, sh, sm, _, _ in MEETING_SLOTS:
                if city == "Auckland":
                    continue  # only with --include-oceania
                if day.weekday() in WEEKDAYS.get(city, DEFAULT_WEEKDAYS):
                    expected.add((city, day.replace(hour=sh, minute=sm)))

    actual = {(e["SUMMARY"].split(" ")[0], start_of(e)) for _, e in all_events(outputs[(alignment, year)], "meetings")}
    assert actual == expected


# -----------------------------------------------------------------------------
# CLI switches
# -----------------------------------------------------------------------------


def test_dry_run_prints_a_monthly_summary_and_writes_nothing(tmp_path, capsys):
    outdir = tmp_path / "out"

    run_cli(outdir, 2027, "academic", "--dry-run")

    shown = capsys.readouterr().out
    assert "Month" in shown and "Focus blocks" in shown and "Glyph Keys" in shown and "Meeting slots" in shown
    rows = {m: line.split() for line in shown.splitlines() for m in re.findall(r"^(\d{4}-\d{2})\b", line)}
    assert sorted(rows) == months_of_year(2027, "academic")
    assert rows["2027-09"] == ["2027-09", "360", "4", "264"]  # 30 days x 12, four Mondays
    assert rows["2028-02"][1] == str(29 * BLOCKS_PER_DAY)
    assert re.search(r"^Total\s+4392\s+52\s+2674$", shown, re.M)
    assert not outdir.exists(), "dry-run must not write files"


def test_dry_run_shows_a_dash_for_a_layer_that_is_switched_off(tmp_path, capsys):
    run_cli(tmp_path / "out", 2027, "academic", "--dry-run", "--no-meetings")
    shown = capsys.readouterr().out
    assert re.search(r"^2027-09\s+360\s+4\s+-$", shown, re.M)


def test_no_focus_flag_skips_the_focus_folder(tmp_path):
    run_cli(tmp_path, 2027, "academic", "--no-focus", "--no-meetings", "--no-ebi48")
    assert sorted(p.name for p in tmp_path.iterdir()) == [MARKER, "seasons_2027.ics"]


def test_no_meetings_flag_skips_the_meetings_folder(tmp_path):
    run_cli(tmp_path, 2027, "academic", "--no-meetings", "--no-ebi48")
    assert sorted(p.name for p in tmp_path.iterdir()) == [MARKER, "focus", "seasons_2027.ics"]


def test_include_oceania_adds_auckland(tmp_path):
    run_cli(tmp_path, 2027, "academic", "--include-oceania", "--no-focus", "--no-ebi48")
    september = read_events(tmp_path / "meetings" / "meetings_2027-09.ics")
    assert any(e["SUMMARY"].startswith("Auckland ") for e in september)
