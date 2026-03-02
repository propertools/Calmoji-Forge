# calmoji/calendar_phases.py

from __future__ import annotations

from datetime import timedelta
from typing import List

from calmoji.calendar_config import (
    DEFAULT_ALIGNMENT,
    get_year_start_date,
    get_semester_phase_definitions,
)
from calmoji.types import Phase


def get_semester_phases(year: int, alignment: str = DEFAULT_ALIGNMENT) -> List[Phase]:
    """
    Return a list of enriched Phase objects for the specified aligned year.

    Each phase includes:
      - concrete start/end datetimes (UTC)
      - symbolic meeting density metadata (e.g., 'normal', 'low', 'none')
    """
    start_date = get_year_start_date(year, alignment)
    phase_defs = get_semester_phase_definitions()

    enriched: List[Phase] = []

    for phase_def in phase_defs:
        start = start_date + timedelta(days=phase_def.start_offset)
        end = start_date + timedelta(days=phase_def.end_offset)

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
                end_offset=phase_def.end_offset,
                emoji=phase_def.emoji,
                start=start,
                end=end,
                allow_meetings=allow,
                meeting_density=density,
                note=f"Auto-tagged density: {density}",
            )
        )

    return enriched
    