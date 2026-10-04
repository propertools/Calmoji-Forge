# calmoji/types.py

"""
🧿 Calmoji Core Types
---------------------
Core symbolic data structures for time modeling.

Design goals:
- UTC-only internal timekeeping (no DST ambiguity)
- Deterministic UIDs for stable re-import
- RFC 5545-friendly serialization (VEVENT lines as list[str])

Conventions:
- All intervals are half-open: [start, end)
- Phase.end is EXCLUSIVE
- All internal datetimes are UTC
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import DefaultDict, List, Literal, Optional

from calmoji.constants import DTSTAMP
from calmoji.ics_text import escape_ics_text
from calmoji.uid import generate_uid

UTC = timezone.utc


# =============================================================================
# Event
# =============================================================================


def _reject_line_breaks(name: str, value: Optional[str]) -> None:
    if value is not None and ("\n" in value or "\r" in value):
        raise ValueError(f"{name} must not contain a line break: {value!r}")


@dataclass
class Event:
    """
    One calendar event (a VEVENT). All datetimes are UTC.

    End rules:

    - Timed event: ``end`` must be after ``start`` (``end <= start`` raises ValueError).
      With no ``end`` the event lasts one hour.
    - All-day event: ``start`` is floored to midnight, and the stored ``end`` is an
      EXCLUSIVE midnight, as DTEND;VALUE=DATE is. With no ``end`` the event lasts one day.
      An ``end`` at exactly midnight is taken as that exclusive boundary, and must be
      after the start date. An ``end`` with a time of day means "through that date"
      (inclusive), so it becomes the next midnight: even on the same date as the start,
      08:00-23:00 on one date is a one-day all-day event. An end date before the start
      date raises ValueError.
    """

    start: datetime
    summary: str
    end: Optional[datetime] = None
    uid: Optional[str] = None
    description: str = ""
    emoji: Optional[str] = None
    all_day: bool = False
    recurrence: Optional[str] = None  # Accepts "FREQ=..." or "RRULE:FREQ=..."
    private: bool = True
    transparent: bool = True

    def __post_init__(self) -> None:
        self.start = self._enforce_utc(self.start)
        if self.end is not None:
            self.end = self._enforce_utc(self.end)

        if self.all_day:
            self.start = self.start.replace(hour=0, minute=0, second=0, microsecond=0)

            if self.end is None:
                self.end = self.start + timedelta(days=1)
            else:
                end_midnight = self.end.replace(hour=0, minute=0, second=0, microsecond=0)

                if self.end == end_midnight:
                    # An end at midnight is the exclusive boundary, and must be after the start date.
                    if self.end <= self.start:
                        raise ValueError(
                            f"All-day event end {self.end:%Y-%m-%d} must be after its start {self.start:%Y-%m-%d} "
                            "(an end at midnight is exclusive)."
                        )
                else:
                    # An end with a time of day means "through that date" (inclusive): the next midnight.
                    if end_midnight < self.start:
                        raise ValueError(
                            f"All-day event end date {end_midnight:%Y-%m-%d} is before its start date "
                            f"{self.start:%Y-%m-%d}."
                        )
                    self.end = end_midnight + timedelta(days=1)
        elif self.end is None:
            self.end = self.start + timedelta(hours=1)
        elif self.end <= self.start:
            raise ValueError(f"Event end {self.end.isoformat()} must be after its start {self.start.isoformat()}.")

        if not self.uid:
            dt_str = self.start.strftime("%Y%m%d") if self.all_day else self.start.strftime("%Y%m%dT%H%M%S")
            label = int(sha256((self.summary + dt_str).encode("utf-8")).hexdigest(), 16) & 0xFFFFFFFF
            self.uid = generate_uid(dt=self.start, label=str(label), namespace="calmoji")

    @staticmethod
    def _enforce_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        if dt.tzinfo != UTC:
            raise ValueError("Event datetimes must be UTC.")
        return dt

    def dtstart(self) -> str:
        if self.all_day:
            return f"DTSTART;VALUE=DATE:{self.start.strftime('%Y%m%d')}"
        return f"DTSTART:{self.start.strftime('%Y%m%dT%H%M%SZ')}"

    def dtend(self) -> str:
        if self.end is None:
            raise ValueError("Event must have an end time (computed in __post_init__).")
        if self.all_day:
            return f"DTEND;VALUE=DATE:{self.end.strftime('%Y%m%d')}"
        return f"DTEND:{self.end.strftime('%Y%m%dT%H%M%SZ')}"

    def to_ics(self) -> list[str]:
        """
        Render this event as VEVENT content lines.

        TEXT properties (SUMMARY, DESCRIPTION) are escaped per RFC 5545 §3.3.11, so no
        value can inject a content line. UID and RRULE aren't TEXT, so they can't be
        escaped; instead they must not contain a line break at all.
        """
        summary = escape_ics_text(f"{self.emoji} {self.summary}" if self.emoji else self.summary)
        _reject_line_breaks("UID", self.uid)
        _reject_line_breaks("RRULE", self.recurrence)

        lines: list[str] = [
            "BEGIN:VEVENT",
            f"UID:{self.uid}",
            f"DTSTAMP:{DTSTAMP}",
            f"SUMMARY:{summary}",
            self.dtstart(),
            self.dtend(),
        ]

        if self.description:
            lines.append(f"DESCRIPTION:{escape_ics_text(self.description)}")

        if self.recurrence:
            rule = self.recurrence.strip()
            if not rule.startswith("RRULE:"):
                rule = f"RRULE:{rule}"
            lines.append(rule)

        lines.append(f"CLASS:{'PRIVATE' if self.private else 'PUBLIC'}")
        lines.append(f"TRANSP:{'TRANSPARENT' if self.transparent else 'OPAQUE'}")
        lines.append("END:VEVENT")
        return lines


# =============================================================================
# Phase
# =============================================================================


@dataclass
class Phase:
    name: str
    start_offset: int
    end_offset: int  # EXCLUSIVE day offset
    emoji: str
    allow_meetings: bool = True
    meeting_density: str = "normal"  # 'none'|'low'|'normal'|'high' (convention)
    note: Optional[str] = None
    start: Optional[datetime] = None  # inclusive
    end: Optional[datetime] = None  # exclusive

    @property
    def duration_days(self) -> Optional[int]:
        if self.start and self.end:
            # end is exclusive
            return (self.end - self.start).days
        return None


PhaseName = Literal[
    "Semester A (Seed)",
    "Winter Break",
    "Semester A (cont.)",
    "Downtime A→B",
    "Semester B (Flame)",
    "Summer Rest",
    "Deep Work Phase",
    "Autumn Drift",
]


# =============================================================================
# PhaseWeekSpan
# =============================================================================


@dataclass(frozen=True)
class PhaseWeekSpan:
    """
    Represents an ISO-week-aligned span (Monday 00:00 UTC) within a Phase.

    - start: Monday 00:00 UTC for the ISO week
    - phase_name: Phase label (string, kept flexible)
    - week_index: zero-based week index within the Phase
    - ritual_type: optional tag for future routing (default 'focus')

    This is a week-grouping helper: from_phase() returns every ISO week that
    touches the Phase (weeks discovered by iterating days in
    [phase.start, phase.end)), as whole weeks. It does not clip to the Phase.
    Focus-block generation does not build on it; focus blocks are clipped to
    the Phase's own dates.
    """

    start: datetime
    phase_name: str
    week_index: int
    ritual_type: str = field(default="focus")

    @property
    def iso_week_label(self) -> str:
        iso_year, iso_week, _ = self.start.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"

    def label(self) -> str:
        return f"{self.phase_name} / Week {self.week_index + 1}"

    @classmethod
    def from_phase(cls, phase: Phase) -> List[PhaseWeekSpan]:
        if phase.start is None or phase.end is None:
            raise ValueError(f"Phase {phase.name} is missing concrete start/end datetimes.")

        # Iterate day by day at midnight UTC (phase.end is exclusive)
        current = phase.start.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=UTC)
        end = phase.end.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=UTC)

        week_map: DefaultDict[tuple[int, int], List[datetime]] = defaultdict(list)

        while current < end:
            iso_year, iso_week, _ = current.isocalendar()
            week_map[(iso_year, iso_week)].append(current)
            current += timedelta(days=1)

        sorted_weeks = sorted(week_map.items(), key=lambda x: min(x[1]))

        spans: List[PhaseWeekSpan] = []
        for idx, (_, days) in enumerate(sorted_weeks):
            monday = min(days) - timedelta(days=min(days).weekday())
            monday = monday.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=UTC)
            spans.append(cls(start=monday, phase_name=phase.name, week_index=idx))

        return spans
