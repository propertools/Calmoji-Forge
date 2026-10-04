# tests/test_focus_blocks_writer.py

import datetime

import pytest

from calmoji.focus_blocks import generate_focus_blocks_for_week
from calmoji.focus_blocks_config import ACTIVE_WEEKDAYS, DEFAULT_ACTIVE_WEEKDAYS, FOCUS_BLOCKS
from calmoji.focus_blocks_writer import write_focus_blocks
from calmoji.ics_writer import unfold_ics_lines
from calmoji.types import Phase, PhaseWeekSpan

UTC = datetime.timezone.utc


def make_phase(name: str, start_date: str, end_date_inclusive: str, emoji: str = "📆") -> Phase:
    """
    Create a Phase from ISO date strings.

    IMPORTANT: Phase.end is EXCLUSIVE.
    This helper accepts an inclusive end date and converts it to exclusive midnight.
    """
    start = datetime.datetime.fromisoformat(start_date).replace(tzinfo=UTC)
    end_inclusive = datetime.datetime.fromisoformat(end_date_inclusive).replace(tzinfo=UTC)
    end_exclusive = end_inclusive + datetime.timedelta(days=1)

    return Phase(
        name=name,
        start=start,
        end=end_exclusive,
        start_offset=0,
        end_offset=(end_exclusive - start).days,
        emoji=emoji,
    )


def test_focus_blocks_respect_active_weekdays():
    # Use the ISO week containing 2025-01-01 (Monday is 2024-12-30)
    week = PhaseWeekSpan(
        start=datetime.datetime(2024, 12, 30, 0, 0, tzinfo=UTC),
        phase_name="Week Check",
        week_index=0,
    )

    events = generate_focus_blocks_for_week(
        week,
        label="Week Check",
        phase_emoji="📆",
        include_glyph_key=False,
    )

    active_days = set(ACTIVE_WEEKDAYS or DEFAULT_ACTIVE_WEEKDAYS)

    assert events, "No focus blocks generated"
    assert all(e.start.weekday() in active_days for e in events), "Found events on inactive weekdays"

    # Expected count: active days within that ISO week * blocks per day
    expected = len(active_days) * len(FOCUS_BLOCKS)
    assert len(events) == expected, f"Expected {expected} events, found {len(events)}"


def test_each_active_day_has_expected_focus_block_count():
    week = PhaseWeekSpan(
        start=datetime.datetime(2024, 12, 30, 0, 0, tzinfo=UTC),
        phase_name="Two Day",
        week_index=0,
    )

    events = generate_focus_blocks_for_week(
        week,
        label="Two Day",
        phase_emoji="📆",
        include_glyph_key=False,
    )

    events_by_day: dict[datetime.date, list] = {}
    for e in events:
        events_by_day.setdefault(e.start.date(), []).append(e)

    active_weekdays = set(ACTIVE_WEEKDAYS or DEFAULT_ACTIVE_WEEKDAYS)

    # Check that every active weekday *present in this week* has exactly len(FOCUS_BLOCKS) events
    for day_offset in range(7):
        d = (week.start + datetime.timedelta(days=day_offset)).date()
        weekday = (week.start + datetime.timedelta(days=day_offset)).weekday()
        if weekday not in active_weekdays:
            continue

        actual = len(events_by_day.get(d, []))
        expected = len(FOCUS_BLOCKS)
        assert actual == expected, f"Expected {expected} events on {d}, found {actual}"


def test_phase_week_span_from_phase_handles_cross_week_ranges():
    # Jan 1..Jan 6 inclusive => end exclusive Jan 7
    phase = make_phase("Edge Case", "2025-01-01", "2025-01-06")

    spans = PhaseWeekSpan.from_phase(phase)

    assert spans, "Expected at least one weekly span"
    # Jan 1 2025 is in ISO week 2025-W01 (Monday 2024-12-30)
    assert spans[0].start == datetime.datetime(2024, 12, 30, 0, 0, tzinfo=UTC)
    assert spans[0].iso_week_label == "2025-W01"

    # Jan 6 2025 is Monday of ISO week 2025-W02, so we should have a second span
    assert spans[-1].start == datetime.datetime(2025, 1, 6, 0, 0, tzinfo=UTC)
    assert spans[-1].iso_week_label == "2025-W02"


def test_last_focus_block_is_block_12_with_torii_in_summary():
    week = PhaseWeekSpan(
        start=datetime.datetime(2024, 12, 30, 0, 0, tzinfo=UTC),
        phase_name="Final Block",
        week_index=0,
    )

    events = generate_focus_blocks_for_week(
        week,
        label="Final Block",
        phase_emoji="🌀",
        include_glyph_key=False,
    )

    final_event = sorted(events, key=lambda e: e.start)[-1]
    assert "Focus Block 12" in final_event.summary
    assert "⛩️" in final_event.summary, f"Expected ⛩️ in summary, got: {final_event.summary!r}"


def _summaries(path):
    return [line for line in unfold_ics_lines(path.read_text(encoding="utf-8")) if line.startswith("SUMMARY:")]


def test_glyph_key_event_written_for_single_monday(tmp_path):
    # Single day: Monday 2025-01-06 (inclusive) => end exclusive 2025-01-07
    phase = make_phase("Glyph Test Phase", "2025-01-06", "2025-01-06", emoji="🧪")

    write_focus_blocks([phase], tmp_path, 2025)

    expected = tmp_path / "focus_glyph_test_phase_2025-01-06_to_2025-01-07.ics"
    assert expected.exists(), f"Expected .ics file not found: {expected}"

    summaries = _summaries(expected)
    glyph = [line for line in summaries if "GLYPH KEY" in line.upper()]
    assert len(glyph) == 1, f"Expected 1 Glyph Key SUMMARY, found {len(glyph)}"
    assert len(summaries) == len(FOCUS_BLOCKS) + 1


def test_no_glyph_key_for_a_phase_without_a_monday(tmp_path):
    # Single day: Saturday 2025-01-04. The Monday of its ISO week is outside the phase.
    phase = make_phase("Saturday Phase", "2025-01-04", "2025-01-04", emoji="🧪")

    write_focus_blocks([phase], tmp_path, 2025)

    summaries = _summaries(tmp_path / "focus_saturday_phase_2025-01-04_to_2025-01-05.ics")
    assert not [line for line in summaries if "GLYPH KEY" in line.upper()]
    assert len(summaries) == len(FOCUS_BLOCKS)


def test_writer_writes_one_file_per_phase_plus_a_consolidated_file(tmp_path):
    phases = [
        make_phase("Phase One", "2025-01-06", "2025-01-12"),
        make_phase("Phase Two", "2025-01-13", "2025-01-19"),
    ]

    written = write_focus_blocks(phases, tmp_path, 2025)

    assert [p.name for p in written] == [
        "focus_phase_one_2025-01-06_to_2025-01-13.ics",
        "focus_phase_two_2025-01-13_to_2025-01-20.ics",
        "focus_all_2025.ics",
    ]
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(p.name for p in written)

    one, two, everything = (_summaries(p) for p in written)
    assert sorted(one + two) == sorted(everything)


def test_writer_sets_calendar_names(tmp_path):
    phase = make_phase("Phase One", "2025-01-06", "2025-01-12")

    one, everything = write_focus_blocks([phase], tmp_path, 2025)

    one_lines = unfold_ics_lines(one.read_text(encoding="utf-8"))
    all_lines = unfold_ics_lines(everything.read_text(encoding="utf-8"))
    assert "X-WR-CALNAME:🧿 calmoji — Focus Blocks — Phase One (UTC)" in one_lines
    assert "X-WR-CALNAME:🧿 calmoji — Focus Blocks (All) 2025 (UTC)" in all_lines


def test_writer_rejects_undated_phase(tmp_path):
    undated = Phase(name="Undated", start_offset=0, end_offset=7, emoji="🧪")

    with pytest.raises(ValueError, match="Undated"):
        write_focus_blocks([undated], tmp_path, 2025)
