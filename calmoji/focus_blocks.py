# calmoji/focus_blocks.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence

from calmoji.focus_blocks_config import ACTIVE_WEEKDAYS, DEFAULT_ACTIVE_WEEKDAYS, FOCUS_BLOCKS
from calmoji.types import Event, Phase, PhaseWeekSpan

UTC = timezone.utc


@dataclass(frozen=True)
class FocusBlockDef:
    """Canonical definition for a daily focus block."""

    number: int
    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int
    emoji: str


# -----------------------------------------------------------------------------
# Config parsing (single source of truth)
# -----------------------------------------------------------------------------

_CACHED_ACTIVE_WEEKDAYS: list[int] | None = None
_CACHED_BLOCK_DEFS: list[FocusBlockDef] | None = None


def _get_active_weekdays() -> list[int]:
    """
    Return active weekdays for focus blocks.

    If ACTIVE_WEEKDAYS is None -> DEFAULT_ACTIVE_WEEKDAYS (usually all 7 days).
    Dedupes while preserving order.
    """
    global _CACHED_ACTIVE_WEEKDAYS
    if _CACHED_ACTIVE_WEEKDAYS is not None:
        return _CACHED_ACTIVE_WEEKDAYS

    days = ACTIVE_WEEKDAYS if ACTIVE_WEEKDAYS is not None else DEFAULT_ACTIVE_WEEKDAYS

    out: list[int] = []
    for d in days:
        if not isinstance(d, int) or not (0 <= d <= 6):
            raise ValueError(f"ACTIVE_WEEKDAYS must contain ints 0..6, got {d!r}")
        out.append(d)

    seen: set[int] = set()
    deduped: list[int] = []
    for d in out:
        if d not in seen:
            seen.add(d)
            deduped.append(d)

    _CACHED_ACTIVE_WEEKDAYS = deduped
    return deduped


def _get_focus_block_defs() -> list[FocusBlockDef]:
    """Parse and validate FOCUS_BLOCKS into typed FocusBlockDef objects."""
    global _CACHED_BLOCK_DEFS
    if _CACHED_BLOCK_DEFS is not None:
        return _CACHED_BLOCK_DEFS

    defs: list[FocusBlockDef] = []
    for entry in FOCUS_BLOCKS:
        if not isinstance(entry, (list, tuple)) or len(entry) != 6:
            raise ValueError(f"FOCUS_BLOCKS entries must be 6-tuples, got: {entry!r}")

        n, sh, sm, eh, em, emoji = entry
        defs.append(
            FocusBlockDef(
                number=int(n),
                start_hour=int(sh),
                start_minute=int(sm),
                end_hour=int(eh),
                end_minute=int(em),
                emoji=str(emoji),
            )
        )

    _CACHED_BLOCK_DEFS = defs
    return defs


# -----------------------------------------------------------------------------
# Window helpers
# -----------------------------------------------------------------------------


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    if dt.tzinfo != UTC:
        raise ValueError("Datetime must be UTC.")
    return dt


def _day_start(dt: datetime) -> datetime:
    """Return 00:00 UTC of the day containing dt."""
    return _ensure_utc(dt).replace(hour=0, minute=0, second=0, microsecond=0)


def _week_window(week: PhaseWeekSpan) -> tuple[datetime, datetime]:
    """
    Return [week_start, week_end_exclusive) where week_start is Monday 00:00 UTC.
    """
    start = _day_start(week.start)
    end_exclusive = start + timedelta(days=7)
    return start, end_exclusive


def _iso_week_label(dt: datetime) -> str:
    """ISO week label such as '2027-W49' for the week containing dt."""
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


# -----------------------------------------------------------------------------
# Event builders (pure: no I/O)
# -----------------------------------------------------------------------------


def _glyph_key_event(monday: datetime, *, label: str, phase_emoji: str) -> Event:
    """All-day 🗝️ Glyph Key marker for the week starting on the given Monday."""
    week_label = _iso_week_label(monday)
    return Event(
        start=monday,
        end=monday + timedelta(days=1),
        summary=f"Glyph Key — {label} — {week_label}",
        description=f"{phase_emoji} — {label} — focus blocks for {week_label} (UTC).",
        emoji="🗝️",
        all_day=True,
    )


def _focus_blocks_for_day(day: datetime, *, label: str, phase_emoji: str) -> list[Event]:
    """Every focus block of one day (00:00 UTC), in block order. Ignores ACTIVE_WEEKDAYS."""
    week_label = _iso_week_label(day)
    events: list[Event] = []

    for bd in _get_focus_block_defs():
        summary = f"{bd.emoji} Focus Block {bd.number} — {label}"
        description = (
            f"{phase_emoji} — {label}\\n"
            f"{bd.emoji} Focus Block {bd.number} "
            f"({bd.start_hour:02d}:{bd.start_minute:02d}–{bd.end_hour:02d}:{bd.end_minute:02d} UTC)\\n"
            f"Week: {week_label} (UTC)"
        )

        events.append(
            Event(
                start=day.replace(hour=bd.start_hour, minute=bd.start_minute),
                end=day.replace(hour=bd.end_hour, minute=bd.end_minute),
                summary=summary,
                description=description,
            )
        )

    return events


# -----------------------------------------------------------------------------
# Generators (pure: no I/O)
# -----------------------------------------------------------------------------


def generate_focus_blocks_for_week(
    week: PhaseWeekSpan,
    *,
    label: str,
    phase_emoji: str,
    include_glyph_key: bool = True,
) -> list[Event]:
    """
    Generate focus block events for one whole ISO week span (Monday to Sunday).

    Notes:
    - Emits blocks only on ACTIVE_WEEKDAYS (or default 7 days).
    - UTC-only.
    - Returns Event objects only.
    - The week is *not* clipped to any Phase. Phase-level generation
      (generate_focus_blocks_for_phase) does not use this function; it clips
      to the phase's own dates.
    """
    week_start, _ = _week_window(week)
    weekdays = set(_get_active_weekdays())

    events: list[Event] = []

    if include_glyph_key:
        events.append(_glyph_key_event(week_start, label=label, phase_emoji=phase_emoji))

    for day_offset in range(7):
        day = week_start + timedelta(days=day_offset)
        if day.weekday() in weekdays:
            events.extend(_focus_blocks_for_day(day, label=label, phase_emoji=phase_emoji))

    return sorted(events, key=lambda e: e.start)


def generate_focus_blocks_for_phase(
    phase: Phase,
    *,
    include_weekly_glyph_keys: bool = True,
) -> list[Event]:
    """
    Generate all focus block events for a Phase, clipped to the Phase.

    Same clipping rule as meeting slots:
    - Emits exactly the blocks whose start falls in [phase.start, phase.end),
      on ACTIVE_WEEKDAYS (or default 7 days).
    - A week that straddles two phases is split between them (each phase gets
      only its own days), so no block is emitted by more than one phase.
    - Emits the all-day 🗝️ Glyph Key marker on each Monday that falls inside
      the Phase, if include_weekly_glyph_keys is True.
    """
    if phase.start is None or phase.end is None:
        raise ValueError(f"Phase {phase.name} is missing start/end datetimes.")

    phase_start = _ensure_utc(phase.start)
    phase_end_excl = _ensure_utc(phase.end)
    weekdays = set(_get_active_weekdays())

    candidates: list[Event] = []

    day = _day_start(phase_start)
    while day < phase_end_excl:
        if include_weekly_glyph_keys and day.weekday() == 0:
            candidates.append(_glyph_key_event(day, label=phase.name, phase_emoji=phase.emoji))
        if day.weekday() in weekdays:
            candidates.extend(_focus_blocks_for_day(day, label=phase.name, phase_emoji=phase.emoji))
        day += timedelta(days=1)

    # The one place the clipping rule lives: start in [phase.start, phase.end).
    clipped = [e for e in candidates if phase_start <= e.start < phase_end_excl]
    return sorted(clipped, key=lambda e: e.start)


def generate_focus_blocks_for_phases(
    phases: Sequence[Phase],
    *,
    include_weekly_glyph_keys: bool = True,
) -> list[Event]:
    """Convenience: generate focus blocks across multiple phases."""
    events: list[Event] = []
    for p in phases:
        events.extend(generate_focus_blocks_for_phase(p, include_weekly_glyph_keys=include_weekly_glyph_keys))
    return sorted(events, key=lambda e: e.start)
