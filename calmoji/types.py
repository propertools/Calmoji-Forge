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

from calmoji.uid import generate_uid

UTC = timezone.utc


# =============================================================================
# Event
# =============================================================================

@dataclass
class Event:
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
            # DTSTART;VALUE=DATE is a date; DTEND;VALUE=DATE is EXCLUSIVE.
            # We store start at midnight, and store end at the exclusive midnight boundary.
            self.start = self.start.replace(hour=0, minute=0, second=0, microsecond=0)

            if self.end is None:
                self.end = self.start + timedelta(days=1)
            else:
                # If caller passes a date-like midnight boundary, assume it's already exclusive.
                # If caller passes a timeful end, treat it as an inclusive end-date and +1 day.
                end_midnight = self.end.replace(hour=0, minute=0, second=0, microsecond=0)

                if end_midnight <= self.start:
                    raise ValueError("All-day event end must be after start.")

                is_midnight_input = (
                    self.end.hour == 0
                    and self.end.minute == 0
                    and self.end.second == 0
                    and self.end.microsecond == 0
                )
                self.end = end_midnight if is_midnight_input else (end_midnight + timedelta(days=1))
        else:
            self.end = self.end or (self.start + timedelta(hours=1))

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
        summary = f"{self.emoji} {self.summary}" if self.emoji else self.summary
        safe_description = self.description.replace("\n", "\\n").replace("\r", "")

        lines: list[str] = [
            "BEGIN:VEVENT",
            f"UID:{self.uid}",
            f"SUMMARY:{summary}",
            self.dtstart(),
            self.dtend(),
        ]

        if self.description:
            lines.append(f"DESCRIPTION:{safe_description}")

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
    end: Optional[datetime] = None    # exclusive

    @property
    def duration_days(self) -> Optional[int]:
        if self.start and self.end:
            # end is exclusive
            return (self.end - self.start).days
        return None


PhaseName = Literal[
    "Seed",
    "Flame",
    "Downtime A→B",
    "Winter Break",
    "Summer Rest",
    "Deep Work Phase",
    "Semester A (Seed)",
    "Semester A (cont.)",
    "Semester B (Flame)",
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
    Emits full ISO weeks whose start occurs in the phase’s covered-week set (weeks discovered by iterating days in [phase.start, phase.end)). Does not clip within-week.
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
    def from_phase(cls, phase: Phase) -> List["PhaseWeekSpan"]:
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

        spans: List["PhaseWeekSpan"] = []
        for idx, (_, days) in enumerate(sorted_weeks):
            monday = min(days) - timedelta(days=min(days).weekday())
            monday = monday.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=UTC)
            spans.append(cls(start=monday, phase_name=phase.name, week_index=idx))

        return spans