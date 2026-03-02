# calmoji/focus_blocks_writer.py

from __future__ import annotations

from pathlib import Path

from calmoji.focus_blocks import generate_focus_blocks_for_week
from calmoji.ics_writer import write_events_to_ics
from calmoji.types import Phase, PhaseWeekSpan
from calmoji.utils import slugify


def write_focus_blocks_weekly(phases: list[Phase], output_dir: Path) -> None:
    """
    Write per-week focus block .ics files for a list of Phases.

    Dumb writer:
      - delegates all event generation to calmoji/focus_blocks.py
      - writes one file per ISO week intersecting each Phase
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for phase in phases:
        if phase.start is None or phase.end is None:
            raise ValueError(f"Phase {phase.name} is missing concrete start/end datetimes.")

        weeks = PhaseWeekSpan.from_phase(phase)

        for week in weeks:
            events = generate_focus_blocks_for_week(
                week,
                label=phase.name,
                phase_emoji=phase.emoji,
                include_glyph_key=True,
            )

            filename = f"{slugify(phase.name)}__{week.iso_week_label}.ics"
            write_events_to_ics(
                events,
                output_dir / filename,
                calname=f"🧿 calmoji — Focus Blocks — {phase.name} — {week.iso_week_label}",
            )