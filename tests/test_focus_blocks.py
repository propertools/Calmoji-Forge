# tests/test_focus_blocks.py

import inspect
from datetime import datetime, timezone

import pytest

from calmoji import focus_blocks
from calmoji.focus_blocks import (
    generate_focus_blocks_for_phase,
    generate_focus_blocks_for_phases,
    generate_focus_blocks_for_week,
)
from calmoji.focus_blocks_config import ACTIVE_WEEKDAYS, DEFAULT_ACTIVE_WEEKDAYS, FOCUS_BLOCKS
from calmoji.types import Phase, PhaseWeekSpan

UTC = timezone.utc


def test_generate_focus_block_events_for_a_week():
    # 2039-W01 starts on Monday 2038-12-27 (UTC)
    week_start = datetime(2038, 12, 27, 0, 0, tzinfo=UTC)
    span = PhaseWeekSpan(start=week_start, phase_name="Deep Focus", week_index=0)

    events = generate_focus_blocks_for_week(span, label="Deep Focus", phase_emoji="🔥")

    assert events, "No focus block events generated"

    # Focus blocks for each active day, and nothing else: no all-day markers
    active_days = ACTIVE_WEEKDAYS if ACTIVE_WEEKDAYS is not None else DEFAULT_ACTIVE_WEEKDAYS
    expected_blocks = len(active_days) * len(FOCUS_BLOCKS)
    assert len(events) == expected_blocks

    assert not any(e.all_day for e in events)
    assert all("Focus Block" in e.summary for e in events)
    assert all(e.start.tzinfo is UTC for e in events)
    assert events[0].start == week_start
    assert events == sorted(events, key=lambda e: e.start)


# -----------------------------------------------------------------------------
# Phase-level generation: clipped to the phase, like meeting slots
# -----------------------------------------------------------------------------


def _phase(name: str, start: str, end_exclusive: str, emoji: str = "🧪") -> Phase:
    s = datetime.fromisoformat(start).replace(tzinfo=UTC)
    e = datetime.fromisoformat(end_exclusive).replace(tzinfo=UTC)
    return Phase(name=name, start_offset=0, end_offset=(e - s).days, emoji=emoji, start=s, end=e)


def test_phase_focus_blocks_are_clipped_to_the_phase():
    # Wed 2025-01-08 up to (not including) Tue 2025-01-14: Wed..Mon, six days.
    phase = _phase("Clip Test", "2025-01-08", "2025-01-14")

    events = generate_focus_blocks_for_phase(phase)

    assert phase.start is not None and phase.end is not None
    assert all(phase.start <= e.start < phase.end for e in events)

    blocks = [e for e in events if not e.all_day]
    assert len(blocks) == 6 * len(FOCUS_BLOCKS)
    assert blocks[0].start == datetime(2025, 1, 8, 0, 0, tzinfo=UTC)
    assert blocks[-1].start == datetime(2025, 1, 13, 22, 0, tzinfo=UTC)
    assert events == sorted(events, key=lambda e: e.start)


def test_a_phase_holds_only_timed_focus_blocks():
    # No all-day markers of any kind (the weekly Glyph Keys were retired in v0.1.3), whatever the weekday.
    for start, end in (("2025-01-08", "2025-01-14"), ("2025-01-04", "2025-01-05"), ("2025-01-06", "2025-01-13")):
        events = generate_focus_blocks_for_phase(_phase("Clip Test", start, end))
        assert events
        assert not any(e.all_day for e in events)
        assert all(e.summary.startswith(tuple(b[5] for b in FOCUS_BLOCKS)) for e in events)
        assert all("Focus Block" in e.summary and "Glyph" not in e.summary for e in events)


def test_phase_end_is_exclusive():
    # Mon 2025-01-06 .. Tue 2025-01-07 exclusive: only Monday, nothing from Tuesday.
    phase = _phase("One Monday", "2025-01-06", "2025-01-07")

    events = generate_focus_blocks_for_phase(phase)

    assert len(events) == len(FOCUS_BLOCKS)
    assert max(e.start for e in events) == datetime(2025, 1, 6, 22, 0, tzinfo=UTC)


def test_the_glyph_key_options_are_gone():
    for function in (generate_focus_blocks_for_week, generate_focus_blocks_for_phase, generate_focus_blocks_for_phases):
        assert not [name for name in inspect.signature(function).parameters if "glyph" in name], function.__name__
    assert not hasattr(focus_blocks, "_glyph_key_event")


def test_phases_that_split_a_week_do_not_duplicate_blocks():
    # Alpha ends and Beta begins on Thursday 2025-01-09, mid ISO week.
    alpha = _phase("Alpha", "2025-01-01", "2025-01-09")
    beta = _phase("Beta", "2025-01-09", "2025-01-20")

    events = generate_focus_blocks_for_phases([alpha, beta])

    starts = [e.start for e in events]
    assert len(starts) == len(set(starts))
    assert len(starts) == 19 * len(FOCUS_BLOCKS)  # Jan 1..Jan 19

    # Each block carries the name of the phase it falls in, and only that phase.
    for e in events:
        assert ("Alpha" in e.summary) == (e.start < datetime(2025, 1, 9, tzinfo=UTC))
        assert ("Beta" in e.summary) == (e.start >= datetime(2025, 1, 9, tzinfo=UTC))


def test_phase_events_match_week_events_for_a_whole_week():
    # A phase that is exactly one Monday-to-Sunday week must produce the same
    # events as the whole-week helper (same summaries, descriptions and UIDs).
    phase = _phase("Whole Week", "2025-01-06", "2025-01-13")
    span = PhaseWeekSpan(start=datetime(2025, 1, 6, 0, 0, tzinfo=UTC), phase_name="Whole Week", week_index=0)

    by_phase = generate_focus_blocks_for_phase(phase)
    by_week = generate_focus_blocks_for_week(span, label="Whole Week", phase_emoji="🧪")

    assert by_phase == by_week


def test_phase_generation_honours_active_weekdays(monkeypatch):
    monkeypatch.setattr(focus_blocks, "ACTIVE_WEEKDAYS", [0, 1, 2, 3, 4])
    monkeypatch.setattr(focus_blocks, "_CACHED_ACTIVE_WEEKDAYS", None)
    phase = _phase("Weekdays", "2025-01-06", "2025-01-13")

    events = generate_focus_blocks_for_phase(phase)

    assert len(events) == 5 * len(FOCUS_BLOCKS)
    assert all(e.start.weekday() < 5 for e in events)


def test_phase_without_dates_is_rejected():
    phase = Phase(name="Undated", start_offset=0, end_offset=7, emoji="🧪")

    with pytest.raises(ValueError, match="Undated"):
        generate_focus_blocks_for_phase(phase)
