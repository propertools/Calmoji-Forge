# calmoji/calendar_config.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from calmoji.types import Phase

UTC = timezone.utc  # stdlib tzinfo

# 🧭 Alignment definitions — single source of truth
ALIGNMENTS = {
    "calendar": lambda year: datetime(year, 1, 1, tzinfo=UTC),
    "academic": lambda year: datetime(year, 9, 1, tzinfo=UTC),
    "fiscal_us": lambda year: datetime(year, 10, 1, tzinfo=UTC),
    "fiscal_eu": lambda year: datetime(year, 1, 1, tzinfo=UTC),
    "japanese_school": lambda year: datetime(year, 4, 1, tzinfo=UTC),
    "indian_fiscal": lambda year: datetime(year, 4, 1, tzinfo=UTC),
    # TODO: placeholder anchors (still UTC-aware)
    "chinese_lunar": lambda year: datetime(year, 2, 10, tzinfo=UTC),
    "islamic_hijri": lambda year: datetime(year, 7, 7, tzinfo=UTC),
}

# 🎯 Constants derived from the keys
ALIGNMENT_MODES = set(ALIGNMENTS.keys())
DEFAULT_ALIGNMENT = "calendar"


def get_year_start_date(year: int, alignment: str = DEFAULT_ALIGNMENT) -> datetime:
    """
    Returns the UTC start datetime for a given alignment mode and year.

    Args:
        year: Year to compute the start date for.
        alignment: One of the predefined alignment modes.

    Returns:
        UTC datetime at midnight for the given alignment's start-of-year.
    """
    fn = ALIGNMENTS.get(alignment, ALIGNMENTS[DEFAULT_ALIGNMENT])
    return fn(year)


def get_semester_phase_definitions() -> List[Phase]:
    """Return symbolic semester phases (offsets are day-based, end_offset is EXCLUSIVE)."""
    return [
        Phase("Semester A (Seed)",      0,   98, "🌱"),  # was 97
        Phase("Winter Break",           98,  112, "❄️"),  # was 111
        Phase("Semester A (cont.)",     112, 137, "🌾"),  # was 136
        Phase("Downtime A→B",           137, 151, "🪷"),  # was 150
        Phase("Semester B (Flame)",     151, 284, "🔥"),  # was 283
        Phase("Summer Rest",            284, 299, "🐚"),  # was 298
        Phase("Deep Work Phase",        299, 341, "🧠"),  # was 340
        Phase("Autumn Drift",           341, 365, "🍂"),  # was 364
    ]
