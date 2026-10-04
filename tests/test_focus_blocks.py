# tests/test_focus_blocks.py

from datetime import datetime, timedelta, timezone

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


def test_generate_focus_block_events_and_glyph_key():
    # 2039-W01 starts on Monday 2038-12-27 (UTC)
    week_start = datetime(2038, 12, 27, 0, 0, tzinfo=UTC)
    span = PhaseWeekSpan(start=week_start, phase_name="Deep Focus", week_index=0)

    events = generate_focus_blocks_for_week(
        span,
        label="Deep Focus",
        phase_emoji="🔥",
        include_glyph_key=True,
    )

    assert events, "No focus block events generated"

    # Expect 1 all-day glyph key + focus blocks for each active day
    active_days = ACTIVE_WEEKDAYS if ACTIVE_WEEKDAYS is not None else DEFAULT_ACTIVE_WEEKDAYS
    expected_blocks = len(active_days) * len(FOCUS_BLOCKS)
    expected_total = expected_blocks + 1  # glyph key

    assert len(events) == expected_total

    # First event should be the all-day Glyph Key marker for the week
    first = events[0]
    assert "Glyph Key" in first.summary
    assert first.all_day is True
    assert first.start == week_start
    assert first.end == week_start + timedelta(days=1)

    # All other events should be timed focus blocks
    blocks = [e for e in events if not e.all_day]
    assert len(blocks) == expected_blocks
    assert all("Focus Block" in e.summary for e in blocks)
    assert all(e.start.tzinfo is UTC for e in events)
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


def test_phase_emits_glyph_key_only_on_mondays_inside_the_phase():
    # The same Wed..Mon phase contains exactly one Monday (2025-01-13, ISO week 3);
    # Monday 2025-01-06 belongs to the week before the phase started.
    phase = _phase("Clip Test", "2025-01-08", "2025-01-14")

    keys = [e for e in generate_focus_blocks_for_phase(phase) if e.all_day]

    assert [k.start for k in keys] == [datetime(2025, 1, 13, 0, 0, tzinfo=UTC)]
    assert "2025-W03" in keys[0].summary
    assert "Glyph Key" in keys[0].summary


def test_phase_without_a_monday_has_no_glyph_key():
    # Saturday 2025-01-04 only.
    phase = _phase("Saturday Only", "2025-01-04", "2025-01-05")

    events = generate_focus_blocks_for_phase(phase)

    assert len(events) == len(FOCUS_BLOCKS)
    assert not any(e.all_day for e in events)


def test_phase_end_is_exclusive():
    # Mon 2025-01-06 .. Tue 2025-01-07 exclusive: only Monday, nothing from Tuesday.
    phase = _phase("One Monday", "2025-01-06", "2025-01-07")

    events = generate_focus_blocks_for_phase(phase)

    assert len(events) == len(FOCUS_BLOCKS) + 1  # blocks + Glyph Key
    assert max(e.start for e in events) == datetime(2025, 1, 6, 22, 0, tzinfo=UTC)


def test_glyph_keys_can_be_switched_off():
    phase = _phase("Keyless", "2025-01-06", "2025-01-13")

    events = generate_focus_blocks_for_phase(phase, include_weekly_glyph_keys=False)

    assert not any(e.all_day for e in events)
    assert len(events) == 7 * len(FOCUS_BLOCKS)


def test_phases_that_split_a_week_do_not_duplicate_blocks():
    # Alpha ends and Beta begins on Thursday 2025-01-09, mid ISO week.
    alpha = _phase("Alpha", "2025-01-01", "2025-01-09")
    beta = _phase("Beta", "2025-01-09", "2025-01-20")

    events = generate_focus_blocks_for_phases([alpha, beta])

    starts = [e.start for e in events if not e.all_day]
    assert len(starts) == len(set(starts))
    assert len(starts) == 19 * len(FOCUS_BLOCKS)  # Jan 1..Jan 19

    # Each Monday gets exactly one Glyph Key, from whichever phase it falls in.
    keys = [(e.start.day, e.summary) for e in events if e.all_day]
    assert [day for day, _ in keys] == [6, 13]
    assert "Alpha" in keys[0][1]
    assert "Beta" in keys[1][1]


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

    blocks = [e for e in events if not e.all_day]
    assert len(blocks) == 5 * len(FOCUS_BLOCKS)
    assert all(e.start.weekday() < 5 for e in blocks)
    # The Monday Glyph Key marks the week regardless of which weekdays are active.
    assert sum(1 for e in events if e.all_day) == 1


def test_phase_without_dates_is_rejected():
    phase = Phase(name="Undated", start_offset=0, end_offset=7, emoji="🧪")

    with pytest.raises(ValueError, match="Undated"):
        generate_focus_blocks_for_phase(phase)
