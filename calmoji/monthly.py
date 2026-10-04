# calmoji/monthly.py

"""
📆 One file per month.

Focus blocks and meeting slots are written one .ics file per UTC month, so every
file fits the import limits of the common calendar apps (see MAX_EVENTS_PER_FILE
and MAX_BYTES_PER_FILE in calmoji.constants).

Each event goes in the month of its DTSTART, in UTC (an all-day event goes by its
date), and nowhere else. A year that doesn't start on the 1st of a month has partial
edge months; the rest of that month lives in the neighbouring year's folder.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, NamedTuple

from calmoji.filenames import monthly_filename
from calmoji.ics_writer import write_events_to_ics
from calmoji.types import Event


class MonthRow(NamedTuple):
    month: str
    focus_blocks: int
    glyph_keys: int
    meeting_slots: int


def month_key(dt: datetime) -> str:
    """'YYYY-MM' of a (UTC) datetime."""
    return f"{dt.year:04d}-{dt.month:02d}"


def bucket_by_month(events: Iterable[Event]) -> Dict[str, List[Event]]:
    """Group events by the UTC month of their start. Keys ascend; each list is sorted by start."""
    buckets: Dict[str, List[Event]] = {}
    for event in events:
        buckets.setdefault(month_key(event.start), []).append(event)
    return {key: sorted(buckets[key], key=lambda e: e.start) for key in sorted(buckets)}


def write_monthly_files(events: Iterable[Event], directory: Path, prefix: str, calname: str) -> List[Path]:
    """
    Write <directory>/<prefix>_<YYYY-MM>.ics for every month that has events.

    Returns the paths written, in month order.
    """
    written: List[Path] = []
    for key, month_events in bucket_by_month(events).items():
        path = directory / monthly_filename(prefix, key)
        write_events_to_ics(month_events, path, calname=calname)
        written.append(path)
    return written


def month_rows(focus_events: Iterable[Event], meeting_events: Iterable[Event]) -> List[MonthRow]:
    """Per-month counts for --dry-run: focus blocks, Glyph Keys and meeting slots."""
    focus = bucket_by_month(focus_events)
    meetings = bucket_by_month(meeting_events)

    rows: List[MonthRow] = []
    for key in sorted(set(focus) | set(meetings)):
        month_focus = focus.get(key, [])
        rows.append(
            MonthRow(
                month=key,
                focus_blocks=sum(1 for e in month_focus if not e.all_day),
                glyph_keys=sum(1 for e in month_focus if e.all_day),
                meeting_slots=len(meetings.get(key, [])),
            )
        )
    return rows
