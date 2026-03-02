# calmoji/generator.py

"""
🧿 Calmoji Event Generator
--------------------------
Generates symbolic calendar events across phases:

  - Focus blocks (via calmoji.focus_blocks)
  - Meeting slots (via calmoji.slot_generator)

This module performs **no I/O**. It returns Event objects
to be rendered/exported elsewhere.
"""

from __future__ import annotations

from typing import List

from calmoji.types import Event, Phase
from calmoji.focus_blocks import generate_focus_blocks_for_phase
from calmoji.slot_generator import generate_meeting_slots


def generate_focus_blocks(phase: Phase) -> List[Event]:
    """Generate all focus block events for a given Phase (no I/O)."""
    return generate_focus_blocks_for_phase(phase)


def get_all_events(phases: List[Phase]) -> List[Event]:
    """
    Generate all events (focus blocks + meeting slots) across phases.

    Returns:
        List[Event]: Sorted Event objects (UTC).
    """
    all_events: List[Event] = []

    for phase in phases:
        all_events.extend(generate_focus_blocks(phase))
        if phase.allow_meetings:
            all_events.extend(generate_meeting_slots(phase))

    return sorted(all_events, key=lambda e: e.start)