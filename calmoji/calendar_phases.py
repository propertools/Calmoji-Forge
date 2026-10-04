# calmoji/calendar_phases.py

from __future__ import annotations

from datetime import timedelta
from typing import List

from calmoji.calendar_config import (
    DEFAULT_ALIGNMENT,
    get_semester_phase_definitions,
    get_year_start_date,
)
from calmoji.types import Phase


def get_semester_phases(year: int, alignment: str = DEFAULT_ALIGNMENT) -> List[Phase]:
    """
    Return a list of enriched Phase objects for the specified aligned year.

    Each phase includes:
      - concrete start/end datetimes (UTC); the last phase ends at the next
        year's anchor, so year N's end is year N+1's start
      - symbolic meeting density metadata (e.g., 'normal', 'low', 'none')
    """
    start_date = get_year_start_date(year, alignment)
    next_start_date = get_year_start_date(year + 1, alignment)
    phase_defs = get_semester_phase_definitions()

    enriched: List[Phase] = []

    for index, phase_def in enumerate(phase_defs):
        start = start_date + timedelta(days=phase_def.start_offset)
        end = start_date + timedelta(days=phase_def.end_offset)
        end_offset = phase_def.end_offset

        # The last phase runs up to the next year's anchor, so consecutive years
        # fit together exactly (in a leap year that is one day past offset 365).
        if index == len(phase_defs) - 1:
            end = next_start_date
            end_offset = (next_start_date - start_date).days

        # Apply heuristic enrichment
        name = phase_def.name
        if any(kw in name for kw in ["Break", "Rest", "Drift"]):
            allow = False
            density = "none"
        elif any(kw in name for kw in ["Downtime", "Prep"]):
            allow = True
            density = "low"
        elif "Deep Work" in name:
            allow = True
            density = "high"
        else:
            allow = True
            density = "normal"

        enriched.append(
            Phase(
                name=name,
                start_offset=phase_def.start_offset,
                end_offset=end_offset,
                emoji=phase_def.emoji,
                start=start,
                end=end,
                allow_meetings=allow,
                meeting_density=density,
                note=f"Auto-tagged density: {density}",
            )
        )

    return enriched
