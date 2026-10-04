# tests/ics_helpers.py
"""Small helpers for reading generated .ics files back in tests."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Dict, List

from calmoji.ics_writer import unfold_ics_lines

UTC = datetime.timezone.utc

Ics = Dict[str, str]


def read_events(path: Path) -> List[Ics]:
    """Parse the VEVENTs of an .ics file into dicts (property name incl. parameters -> value)."""
    events: List[Ics] = []
    current = None
    for line in unfold_ics_lines(path.read_text(encoding="utf-8")):
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT":
            assert current is not None
            events.append(current)
            current = None
        elif current is not None:
            name, _, value = line.partition(":")
            assert name not in current or name == "RRULE", f"repeated property {name}"
            current[name] = value
    return events


def header_lines(path: Path) -> List[str]:
    """The VCALENDAR lines before the first VEVENT."""
    lines = unfold_ics_lines(path.read_text(encoding="utf-8"))
    return lines[: lines.index("BEGIN:VEVENT")] if "BEGIN:VEVENT" in lines else lines


def is_all_day(event: Ics) -> bool:
    return "DTSTART;VALUE=DATE" in event


def start_of(event: Ics) -> datetime.datetime:
    if is_all_day(event):
        return datetime.datetime.strptime(event["DTSTART;VALUE=DATE"], "%Y%m%d").replace(tzinfo=UTC)
    return datetime.datetime.strptime(event["DTSTART"], "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)


def end_of(event: Ics) -> datetime.datetime:
    if is_all_day(event):
        return datetime.datetime.strptime(event["DTEND;VALUE=DATE"], "%Y%m%d").replace(tzinfo=UTC)
    return datetime.datetime.strptime(event["DTEND"], "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
