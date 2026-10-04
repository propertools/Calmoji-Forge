# tests/test_focus_blocks.py

from datetime import datetime, timedelta, timezone

from calmoji.focus_blocks import generate_focus_blocks_for_week
from calmoji.focus_blocks_config import ACTIVE_WEEKDAYS, DEFAULT_ACTIVE_WEEKDAYS, FOCUS_BLOCKS
from calmoji.types import PhaseWeekSpan

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
