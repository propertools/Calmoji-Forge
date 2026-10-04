# calmoji/slot_generator.py

"""
🕒 Meeting Slot Generator
-------------------------
Emits one meeting slot Event per valid weekday per configured city/time block
across the full span of a Phase.

No cadence gating. No recurrence logic. The generator produces a dense palette
of available slots; the user picks and books from it. Recurring collaborations
are managed by the user in a separate calendar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Set

from calmoji.ebi48 import get_emoji_for_time
from calmoji.meeting_slots import MEETING_SLOTS
from calmoji.types import Event, Phase

UTC = timezone.utc


# ── City-specific valid weekdays (0=Monday, 6=Sunday) ───────────────────────

CITY_WEEKDAYS: dict[str, Set[int]] = {
    "Mecca": {6, 0, 1, 2, 3},  # Sunday–Thursday
}

DEFAULT_WEEKDAYS: Set[int] = {0, 1, 2, 3, 4}  # Monday–Friday


# ── Slot definition ─────────────────────────────────────────────────────────


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


# ── Internal helpers ────────────────────────────────────────────────────────


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
    """Parse MEETING_SLOTS config into typed MeetingSlot objects."""
    slots: List[MeetingSlot] = []
    for raw in MEETING_SLOTS:
        city, sh, sm, eh, em, desc = raw
        slots.append(MeetingSlot(city, sh, sm, eh, em, desc))
    return slots


# ── Generator ───────────────────────────────────────────────────────────────


def generate_meeting_slots(
    phase: Phase,
    *,
    include_oceania: bool = False,
) -> List[Event]:
    """
    Generate meeting slot Events for every valid weekday in a Phase.

    - If phase.allow_meetings is False, returns [].
    - Iterates day-by-day at midnight UTC (no time-carry surprises).
    - Emits all configured city slots on each valid day.
    - No cadence gating — every valid day gets slots.

    Args:
        phase: Phase with concrete UTC start/end.
        include_oceania: Whether to include Auckland slots.

    Returns:
        Sorted list of Event objects.
    """
    if phase.start is None or phase.end is None:
        raise ValueError(f"Phase {phase.name} is missing concrete start/end datetimes.")

    if not phase.allow_meetings:
        return []

    phase_start = _normalize_day_start(phase.start)
    phase_end_excl = _normalize_day_start(phase.end)

    slots = _slots_from_config()
    events: List[Event] = []

    for day in _iter_days_exclusive(phase_start, phase_end_excl):
        for s in slots:
            if s.city == "Auckland" and not include_oceania:
                continue

            if not is_valid_slot_day(s.city, day.weekday()):
                continue

            start_dt = day.replace(hour=s.start_hour, minute=s.start_minute)
            end_dt = day.replace(hour=s.end_hour, minute=s.end_minute)

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
