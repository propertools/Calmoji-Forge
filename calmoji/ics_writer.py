# calmoji/ics_writer.py

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Optional, Sequence, Iterable

from calmoji.ebi48 import get_emoji_for_time
from calmoji.types import Event, Phase
from calmoji.uid import generate_uid
from calmoji.utils import get_first_weekday_of_year


# =============================================================================
# VCALENDAR helpers
# =============================================================================

def create_ics_header(
    *,
    calname: str = "🧿 calmoji calendar",
    version: str = "",
    comments: Optional[Sequence[str]] = None,
) -> list[str]:
    full_name = f"{calname} {version}".strip()
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "PRODID:-//Proper Tools SRL//calmoji//EN",
        f"NAME:{full_name}",
        f"X-WR-CALNAME:{full_name}",
        "X-WR-TIMEZONE:UTC",
        "METHOD:PUBLISH",
    ]
    if comments:
        lines.extend([f"COMMENT:{c}" for c in comments])
    return lines


def create_ics_footer() -> list[str]:
    return ["END:VCALENDAR"]


# =============================================================================
# RFC 5545 line folding (75 octets)
# =============================================================================

def fold_ics_line(line: str, limit_octets: int = 75) -> str:
    """
    Fold one logical iCalendar content line per RFC 5545 §3.1 (75 octets max).

    - limit is in octets (bytes), not Python characters
    - folds on character boundaries (UTF-8 safe)
    - continuation lines begin with a single space
    - folded physical lines are joined with CRLF
    """
    if limit_octets < 10:
        raise ValueError("limit_octets is unrealistically small for RFC 5545 folding.")

    if len(line.encode("utf-8")) <= limit_octets:
        return line

    out: list[str] = []
    remaining = line

    while remaining:
        prefix = remaining
        while len(prefix.encode("utf-8")) > limit_octets:
            prefix = prefix[:-1]
            if not prefix:
                raise ValueError("Unable to fold ICS line safely (limit too small).")

        out.append(prefix)
        remaining = remaining[len(prefix):]
        if remaining:
            remaining = " " + remaining  # RFC continuation marker

    return "\r\n".join(out)


def fold_lines(lines: Sequence[str]) -> str:
    """Fold logical lines into CRLF-separated physical lines."""
    return "\r\n".join(fold_ics_line(line) for line in lines)


def unfold_ics_lines(content: str) -> list[str]:
    """
    Unfold ICS text by joining continuation lines.
    Lines beginning with a single space are continuations of the prior line.
    """
    raw_lines = content.splitlines()
    unfolded: list[str] = []

    for i, line in enumerate(raw_lines):
        if line.startswith(" "):
            if not unfolded:
                raise ValueError(f"Malformed ICS: continuation line on line {i + 1} with no prior content.")
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)

    return unfolded


# =============================================================================
# File writer
# =============================================================================

def write_events_to_ics(
    events: Sequence[Event],
    filename: str | Path,
    *,
    header: bool = True,
    footer: bool = True,
    calname: str = "🧿 calmoji calendar",
    version: str = "",
    comments: Optional[Sequence[str]] = None,
    sort_by_start: bool = False,
) -> None:
    """
    Write events to an .ics file (RFC 5545-ish, line-folded, CRLF).

    Args:
        events: Sequence of Event objects.
        filename: Output path.
        header/footer: Whether to include VCALENDAR wrapper.
        calname/version/comments: Metadata for VCALENDAR.
        sort_by_start: If True, writes events in start-time order (diff stability).
    """
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    seq: Iterable[Event] = events
    if sort_by_start:
        seq = sorted(events, key=lambda e: e.start)

    with path.open("w", encoding="utf-8", newline="") as f:
        if header:
            f.write(
                fold_lines(create_ics_header(calname=calname, version=version, comments=comments))
                + "\r\n"
            )

        for i, event in enumerate(seq):
            try:
                f.write(fold_lines(event.to_ics()) + "\r\n")
            except Exception as e:
                raise ValueError(f"Failed to render event at index {i}: {event}") from e

        if footer:
            f.write(fold_lines(create_ics_footer()) + "\r\n")


# =============================================================================
# Higher-level outputs
# =============================================================================

def write_semester_blocks(phases: Sequence[Phase], filename: Optional[str] = None) -> None:
    """
    Emit one all-day VEVENT per Phase.

    For all-day VEVENTs, DTEND is exclusive and Phase.end is already exclusive.
    We therefore write DTEND = phase.end.
    """
    phases = list(phases)
    if not phases:
        raise ValueError("write_semester_blocks: phases list is empty.")

    if filename is None:
        anchor_year = phases[0].start.year if phases[0].start else "unknown"
        filename = f"output/semester_phases_{anchor_year}.ics"

    events: list[Event] = []
    for phase in phases:
        if phase.start is None or phase.end is None:
            raise ValueError(f"Phase {phase.name} is missing start/end datetimes.")

        events.append(
            Event(
                start=phase.start,
                end=phase.end, # exclusive
                summary=phase.name,
                description=f"{phase.emoji} — {phase.name}",
                emoji=phase.emoji,
                all_day=True,
            )
        )

    write_events_to_ics(
        events,
        filename,
        calname="🧿 calmoji — Semester Phases (UTC)",
        sort_by_start=True,
    )


def write_ebi48_layer(
    target_path: str | Path,
    year: int,
    *,
    recurring: bool = True,
    expanded: bool = False,
) -> None:
    """
    Write the EBI48 symbolic emoji layer as an .ics file.

    Modes:
      - recurring=True: one event per slot with weekly RRULE COUNT=52
      - expanded=True: emit 52 explicit instances per slot (bigger file)

    EBI48 is UTC-fixed. It should not shift with local time.
    """
    if recurring and expanded:
        raise ValueError("Choose either recurring or expanded mode, not both.")

    ref_day = get_first_weekday_of_year(year, weekday=5)  # Saturday anchor (UTC)

    comments = [
        "EBI48 is a deterministic, symbolic emoji-based time layer.",
        "It recurs weekly and does not shift with local time.",
        "See: https://ebi48.org/",
    ]

    events: list[Event] = []

    # All-day glyph key marker
    events.append(
        Event(
            start=ref_day,
            end=ref_day + datetime.timedelta(days=1),
            summary="Glyph Key — this week (EBI48)",
            description="Symbolic marker: this calendar encodes canonical EBI48 slot glyphs (UTC-fixed).",
            emoji="🗝️",
            all_day=True,
            uid=generate_uid(dt=ref_day, label="glyph-key", namespace="ebi48"),
        )
    )

    for hour in range(24):
        for minute in (5, 35):
            base_start = ref_day.replace(hour=hour, minute=minute, second=0, microsecond=0)
            base_end = base_start + datetime.timedelta(minutes=25)
            emoji, label = get_emoji_for_time(base_start)

            summary = f"{emoji} {label} — EBI48"
            description = (
                f"{emoji} {label} — Canonical EBI48 time at {hour:02d}:{minute:02d} UTC\\n"
                "This slot is part of the EBI48 symbolic clock.\\n"
                "🕒 UTC only — times do not shift with local time.\\n"
                f"v{year} — https://ebi48.org"
            )

            if expanded:
                for w in range(52):
                    inst_start = base_start + datetime.timedelta(weeks=w)
                    inst_end = base_end + datetime.timedelta(weeks=w)
                    events.append(
                        Event(
                            start=inst_start,
                            end=inst_end,
                            summary=summary,
                            description=description,
                            emoji=emoji,
                            uid=generate_uid(dt=inst_start, label=summary, namespace="ebi48"),
                        )
                    )
            else:
                events.append(
                    Event(
                        start=base_start,
                        end=base_end,
                        summary=summary,
                        description=description,
                        emoji=emoji,
                        recurrence=("FREQ=WEEKLY;COUNT=52" if recurring else None),
                        uid=generate_uid(dt=base_start, label=summary, namespace="ebi48"),
                    )
                )

    write_events_to_ics(
        events,
        target_path,
        calname=f"🧿 calmoji — EBI48 Clock (UTC) v{year}",
        comments=comments,
        sort_by_start=True,
    )



def generate_ics_file(start: datetime.datetime, output) -> None:
    """
    Backwards-compatible stream writer.

    Writes a full VCALENDAR to a writable text stream (e.g. io.StringIO).
    This function CLIPS output to the calendar year [Jan 1, Jan 1 next year).
    """
    from datetime import timezone
    from calmoji.calendar_phases import get_semester_phases
    from calmoji.generator import get_all_events

    # Normalize to UTC + derive year window
    year = start.year
    year_start = datetime.datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    year_end = datetime.datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    phases = get_semester_phases(year, alignment="calendar")
    events = get_all_events(phases)

    # ✅ Clip by DTSTART window to satisfy test_2039 semantics
    events = [e for e in events if (e.start >= year_start and e.start < year_end)]

    output.write(fold_lines(create_ics_header(calname="🧿 calmoji calendar")) + "\r\n")
    for i, event in enumerate(sorted(events, key=lambda e: e.start)):
        try:
            output.write(fold_lines(event.to_ics()) + "\r\n")
        except Exception as e:
            raise ValueError(f"Failed to render event at index {i}: {event}") from e
    output.write(fold_lines(create_ics_footer()) + "\r\n")
