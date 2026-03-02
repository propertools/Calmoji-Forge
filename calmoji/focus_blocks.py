# calmoji/focus_blocks.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Sequence

from calmoji.focus_blocks_config import FOCUS_BLOCKS, ACTIVE_WEEKDAYS, DEFAULT_ACTIVE_WEEKDAYS
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
# Week window helpers
# -----------------------------------------------------------------------------

def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    if dt.tzinfo != UTC:
        raise ValueError("Datetime must be UTC.")
    return dt


def _week_window(week: PhaseWeekSpan) -> tuple[datetime, datetime]:
    """
    Return [week_start, week_end_exclusive) where week_start is Monday 00:00 UTC.
    """
    start = _ensure_utc(week.start).replace(hour=0, minute=0, second=0, microsecond=0)
    end_exclusive = start + timedelta(days=7)
    return start, end_exclusive


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
    Generate focus block events for a single ISO week span.

    Notes:
    - Emits blocks only on ACTIVE_WEEKDAYS (or default 7 days).
    - UTC-only.
    - Returns Event objects only.
    """
    week_start, week_end_excl = _week_window(week)
    weekdays = set(_get_active_weekdays())
    defs = _get_focus_block_defs()

    events: list[Event] = []

    if include_glyph_key:
        events.append(
            Event(
                start=week_start,
                end=week_start + timedelta(days=1),
                summary=f"Glyph Key — {label} — {week.iso_week_label}",
                description=f"{phase_emoji} — {label} — focus blocks for {week.iso_week_label} (UTC).",
                emoji="🗝️",
                all_day=True,
            )
        )

    for day_offset in range(7):
        day = week_start + timedelta(days=day_offset)
        if day.weekday() not in weekdays:
            continue

        for bd in defs:
            start_dt = day.replace(hour=bd.start_hour, minute=bd.start_minute)
            end_dt = day.replace(hour=bd.end_hour, minute=bd.end_minute)

            # Sanity guard (should always be true if PhaseWeekSpan.start is correct)
            if not (week_start <= start_dt < week_end_excl):
                continue

            summary = f"{bd.emoji} Focus Block {bd.number} — {label}"
            description = (
                f"{phase_emoji} — {label}\\n"
                f"{bd.emoji} Focus Block {bd.number} "
                f"({bd.start_hour:02d}:{bd.start_minute:02d}–{bd.end_hour:02d}:{bd.end_minute:02d} UTC)\\n"
                f"Week: {week.iso_week_label} (UTC)"
            )

            events.append(
                Event(
                    start=start_dt,
                    end=end_dt,
                    summary=summary,
                    description=description,
                )
            )

    return sorted(events, key=lambda e: e.start)


def generate_focus_blocks_for_phase(
    phase: Phase,
    *,
    include_weekly_glyph_keys: bool = True,
) -> list[Event]:
    """
    Generate all focus block events for an entire Phase.

    Design choice (coherence > precision):
    - Emits *whole-week* focus blocks for each ISO week intersecting the Phase.
    - Does not clip partial weeks to phase boundaries.
    """
    if phase.start is None or phase.end is None:
        raise ValueError(f"Phase {phase.name} is missing start/end datetimes.")

    weeks = PhaseWeekSpan.from_phase(phase)
    events: list[Event] = []

    for w in weeks:
        events.extend(
            generate_focus_blocks_for_week(
                w,
                label=phase.name,
                phase_emoji=phase.emoji,
                include_glyph_key=include_weekly_glyph_keys,
            )
        )

    return sorted(events, key=lambda e: e.start)


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