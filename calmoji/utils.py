# calmoji/utils.py

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import List, Union

from calmoji.types import Phase, PhaseWeekSpan

UTC = timezone.utc


def coerce_to_utc(dt: datetime) -> datetime:
    """
    Ensure a datetime is timezone-aware and in UTC.

    - If naive, assume UTC.
    - If tz-aware but not UTC, raise.
    """
    if not isinstance(dt, datetime):
        raise TypeError(f"Expected datetime, got {type(dt).__name__}")

    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)

    # Be permissive for tzinfo objects that represent UTC offset 0
    if dt.utcoffset() != timedelta(0):
        raise ValueError("Input datetime must be UTC.")

    # Normalize tzinfo to the stdlib UTC singleton for consistency
    return dt.astimezone(UTC)


def format_datetime(dt: datetime) -> str:
    """Format datetime as an ICS UTC timestamp (YYYYMMDDTHHMMSSZ)."""
    dt = coerce_to_utc(dt)
    return dt.strftime("%Y%m%dT%H%M%SZ")


def format_range_slug(start_date: datetime, end_date: datetime) -> str:
    """Generate a YYYY-MM-DD_to_YYYY-MM-DD slug."""
    return f"{start_date:%Y-%m-%d}_to_{end_date:%Y-%m-%d}"


def get_first_weekday_of_year(year: int, weekday: Union[str, int]) -> datetime:
    """
    Return the first occurrence of the specified weekday in the given year at 00:00 UTC.

    weekday can be:
      - int: 0..6 (Mon..Sun)
      - str: 'mon'/'monday' ... 'sun'/'sunday'
    """
    weekday_map = {
        "monday": 0,
        "mon": 0,
        "tuesday": 1,
        "tue": 1,
        "wednesday": 2,
        "wed": 2,
        "thursday": 3,
        "thu": 3,
        "friday": 4,
        "fri": 4,
        "saturday": 5,
        "sat": 5,
        "sunday": 6,
        "sun": 6,
    }

    if isinstance(weekday, str):
        wd = weekday.lower().strip()
        if wd not in weekday_map:
            raise ValueError(f"Invalid weekday name: {weekday!r}")
        target_wd = weekday_map[wd]
    elif isinstance(weekday, int) and 0 <= weekday <= 6:
        target_wd = weekday
    else:
        raise ValueError(f"Weekday must be int [0–6] or valid name/abbr, got: {weekday!r}")

    d = datetime(year, 1, 1, 0, 0, tzinfo=UTC)
    delta = (target_wd - d.weekday()) % 7
    return d + timedelta(days=delta)


def get_first_monday_on_or_after(d: datetime) -> datetime:
    """Return the first Monday on or after the given date (preserving time + tz)."""
    d = coerce_to_utc(d)
    days_ahead = (0 - d.weekday()) % 7
    return d + timedelta(days=days_ahead)


def slugify(value: str, allow_unicode: bool = False) -> str:
    """Convert strings to safe slugs suitable for filenames or URLs."""
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "_", value)


def group_phase_days_by_week(phase: Phase) -> List[PhaseWeekSpan]:
    """
    Return ISO-week-aligned PhaseWeekSpan objects for a given Phase.

    Delegates to PhaseWeekSpan.from_phase() (single source of truth).
    """
    return PhaseWeekSpan.from_phase(phase)


def format_time_for_tz(dt: datetime, tz_name: str) -> str:
    """Placeholder for future implementation."""
    raise NotImplementedError("Timezone formatting not yet implemented.")
