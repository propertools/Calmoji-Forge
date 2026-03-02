# tests/test_utils.py

import datetime
import pytest

from calmoji.types import Phase, PhaseWeekSpan
from calmoji.utils import get_first_monday_on_or_after, get_first_weekday_of_year, group_phase_days_by_week
from calmoji.ics_writer import fold_ics_line, unfold_ics_lines

UTC = datetime.timezone.utc


def test_first_monday_on_or_after_basic():
    d = datetime.datetime(2024, 9, 15, tzinfo=UTC)  # Sunday
    result = get_first_monday_on_or_after(d)
    assert result.weekday() == 0
    assert result.strftime("%Y-%m-%d") == "2024-09-16"

    d2 = datetime.datetime(2024, 9, 16, tzinfo=UTC)  # Already Monday
    assert get_first_monday_on_or_after(d2) == d2


def test_first_weekday_of_year_by_name():
    # New API returns 00:00 UTC (not 00:05 anymore)
    result = get_first_weekday_of_year(2025, "Saturday")
    assert result.weekday() == 5
    assert result.strftime("%Y-%m-%d %H:%M") == "2025-01-04 00:00"

    result = get_first_weekday_of_year(2025, "Monday")
    assert result.weekday() == 0
    assert result.strftime("%Y-%m-%d %H:%M") == "2025-01-06 00:00"


def test_first_weekday_of_year_by_abbr():
    assert get_first_weekday_of_year(2025, "fri").weekday() == 4  # Friday
    assert get_first_weekday_of_year(2025, "thu").weekday() == 3  # Thursday
    assert get_first_weekday_of_year(2025, "wed").weekday() == 2  # Wednesday

def test_first_weekday_of_year_by_int():
    for i in range(7):
        result = get_first_weekday_of_year(2025, i)
        assert result.weekday() == i


def test_first_weekday_of_year_invalid():
    with pytest.raises(ValueError):
        get_first_weekday_of_year(2025, "Blursday")

    with pytest.raises(ValueError):
        get_first_weekday_of_year(2025, 7)

    with pytest.raises(ValueError):
        get_first_weekday_of_year(2025, -1)


def test_group_phase_days_by_week_basic():
    """
    With Phase.end exclusive, a phase from Jan 1 -> Jan 4 includes Jan 1,2,3.
    Ensure PhaseWeekSpan grouping returns at least one week span with correct ISO label.
    """
    phase = Phase(
        name="Basic",
        start=datetime.datetime(2025, 1, 1, tzinfo=UTC),
        end=datetime.datetime(2025, 1, 4, tzinfo=UTC),  # EXCLUSIVE
        start_offset=0,
        end_offset=3,
        emoji="🔑",
    )

    week_spans = group_phase_days_by_week(phase)
    assert len(week_spans) == 1
    assert isinstance(week_spans[0], PhaseWeekSpan)

    # Jan 1, 2025 is in ISO week 2025-W01; PhaseWeekSpan.start is Monday 00:00 UTC of that ISO week
    assert week_spans[0].iso_week_label == "2025-W01"
    assert week_spans[0].start.weekday() == 0
    assert week_spans[0].start.tzinfo is UTC


def test_fold_and_unfold_roundtrip():
    logical_line = (
        "DESCRIPTION:"
        + "This is a long description that should be folded over multiple lines according to RFC 5545 specifications."
        * 2
    )
    folded = fold_ics_line(logical_line)
    assert "\r\n" in folded
    assert any(line.startswith(" ") for line in folded.splitlines()[1:])  # continuation lines

    unfolded = unfold_ics_lines(folded)
    assert isinstance(unfolded, list)
    assert unfolded[0] == logical_line


def test_fold_ics_line_with_short_input():
    short_line = "SUMMARY:Hello"
    folded = fold_ics_line(short_line)
    assert folded == short_line


def test_unfold_ics_lines_with_no_folds():
    lines = [
        "BEGIN:VEVENT",
        "SUMMARY:Short event",
        "END:VEVENT",
    ]
    unfolded = unfold_ics_lines("\r\n".join(lines))
    assert unfolded == lines


def test_unfold_ics_lines_with_malformed_continuation():
    malformed = " Second line with no leader"
    with pytest.raises(ValueError):
        unfold_ics_lines(malformed)