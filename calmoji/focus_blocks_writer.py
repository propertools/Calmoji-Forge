# calmoji/focus_blocks_writer.py

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from calmoji.focus_blocks import generate_focus_blocks_for_phase
from calmoji.ics_writer import write_events_to_ics
from calmoji.types import Event, Phase
from calmoji.utils import format_range_slug, slugify


def write_focus_blocks(phases: Sequence[Phase], output_dir: Path, year: int) -> list[Path]:
    """
    Write focus block .ics files for a year's Phases: one file per phase, then
    one consolidated file for the whole year.

    Dumb writer:
      - delegates all event generation to calmoji/focus_blocks.py
      - writes focus_<phase>_<from>_to_<to>.ics for each Phase (named like the
        meeting-slot files)
      - writes focus_all_<year>.ics holding exactly the union of those events,
        sorted by start

    Returns the paths written, in write order.
    """
    written: list[Path] = []
    all_events: list[Event] = []

    for phase in phases:
        if phase.start is None or phase.end is None:
            raise ValueError(f"Phase {phase.name} is missing concrete start/end datetimes.")

        events = generate_focus_blocks_for_phase(phase)
        all_events.extend(events)

        target = output_dir / f"focus_{slugify(phase.name)}_{format_range_slug(phase.start, phase.end)}.ics"
        write_events_to_ics(events, target, calname=f"🧿 calmoji — Focus Blocks — {phase.name} (UTC)")
        written.append(target)

    consolidated = output_dir / f"focus_all_{year}.ics"
    write_events_to_ics(
        sorted(all_events, key=lambda e: e.start),
        consolidated,
        calname=f"🧿 calmoji — Focus Blocks (All) {year} (UTC)",
    )
    written.append(consolidated)

    return written
