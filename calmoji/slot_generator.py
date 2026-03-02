# calmoji/slot_generator.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Iterable, Set, Tuple

from calmoji.ebi48 import get_emoji_for_time
from calmoji.meeting_slots import MEETING_SLOTS
from calmoji.types import Event, Phase

UTC = timezone.utc


# City-specific valid weekdays (0 = Monday, 6 = Sunday)
# Default for unspecified cities: Monday–Friday
CITY_WEEKDAYS: dict[str, Set[int]] = {
    "Mecca": {6, 0, 1, 2, 3},  # Sunday–Thursday
}


DEFAULT_WEEKDAYS: Set[int] = {0, 1, 2, 3, 4}


@dataclass(frozen=True)
class MeetingSlot:
    city: str
    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int
    local_desc: str


def is_valid_slot_day(city: str, weekday: int) -> bool:
    """Return True if a meeting slot is valid on this weekday for the given city."""
    return weekday in CITY_WEEKDAYS.get(city, DEFAULT_WEEKDAYS)


def _normalize_day_start(dt: datetime) -> datetime:
    """Force a datetime to 00:00 UTC of its date."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    if dt.tzinfo != UTC:
        raise ValueError("Phase datetimes must be UTC.")
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _iter_days_exclusive(start: datetime, end_exclusive: datetime) -> Iterable[datetime]:
    """Yield 00:00 UTC for each day in [start, end_exclusive)."""
    cur = _normalize_day_start(start)
    end_day = _normalize_day_start(end_exclusive)
    while cur < end_day:
        yield cur
        cur += timedelta(days=1)


def _slots_from_config() -> List[MeetingSlot]:
    slots: List[MeetingSlot] = []
    for raw in MEETING_SLOTS:
        city, sh, sm, eh, em, desc = raw
        slots.append(MeetingSlot(city, sh, sm, eh, em, desc))
    return slots


def generate_meeting_slots(
    phase: Phase,
    *,
    include_oceania: bool = False,
    interval_weeks: int = 3,
    max_cycles: Optional[int] = None,
) -> List[Event]:
    """
    Generate meeting slot Events for a given Phase.

    Stabilized semantics:
    - If phase.allow_meetings is False, returns [].
    - Iterates day-by-day at midnight UTC (no time-carry surprises).
    - Cadence is applied per ISO week bucket:
        * "interval_weeks=3" means: emit *all* valid weekdays in every 3rd week,
          anchored to the phase start week.
    - If max_cycles is set, limits the number of emitted cadence weeks.

    Args:
        phase: Phase with concrete UTC start/end.
        include_oceania: Whether to include Auckland slots.
        interval_weeks: Emit slots every N weeks (default 3).
        max_cycles: Optional cap on number of emitted cadence weeks.

    Returns:
        Sorted list of Event objects.
    """
    if phase.start is None or phase.end is None:
        raise ValueError(f"Phase {phase.name} is missing concrete start/end datetimes.")

    if not phase.allow_meetings:
        return []

    if interval_weeks < 1:
        raise ValueError("interval_weeks must be >= 1")

    phase_start = _normalize_day_start(phase.start)
    phase_end_excl = _normalize_day_start(phase.end)

    # Anchor cadence to Monday 00:00 UTC of the phase start week
    anchor_monday = phase_start - timedelta(days=phase_start.weekday())
    anchor_monday = anchor_monday.replace(hour=0, minute=0, second=0, microsecond=0)

    slots = _slots_from_config()

    events: List[Event] = []
    seen_cycles: Set[int] = set()

    for day in _iter_days_exclusive(phase_start, phase_end_excl):
        weeks_since_anchor = (day - anchor_monday).days // 7

        # This decides whether *this week* is "on" or "off"
        if (weeks_since_anchor % interval_weeks) != 0:
            continue

        cycle_index = weeks_since_anchor // interval_weeks
        if max_cycles is not None and cycle_index >= max_cycles:
            break

        # Track cycles for sanity/debugging (not required, but useful)
        seen_cycles.add(cycle_index)

        for s in slots:
            if s.city == "Auckland" and not include_oceania:
                continue

            if not is_valid_slot_day(s.city, day.weekday()):
                continue

            start_dt = day.replace(hour=s.start_hour, minute=s.start_minute)
            end_dt = day.replace(hour=s.end_hour, minute=s.end_minute)

            # EBI48 mapping is intentionally strict: must land on :05 or :35.
            emoji, face_name = get_emoji_for_time(start_dt)

            summary = f"{s.city} {emoji} {face_name} Slot ({s.local_desc})"
            description = f"{phase.emoji} — {phase.name}"

            events.append(
                Event(
                    start=start_dt,
                    end=end_dt,
                    summary=summary,
                    description=description,
                )
            )

    return sorted(events, key=lambda e: e.start)