# calmoji/ics_writer.py

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Iterable, Optional, Sequence

from calmoji.calendar_config import get_year_start_date
from calmoji.constants import CALNAME_EBI48, CALNAME_PHASES, EBI48_URL
from calmoji.ebi48 import get_emoji_for_time
from calmoji.types import Event, Phase
from calmoji.uid import generate_uid

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
        remaining = remaining[len(prefix) :]
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
            f.write(fold_lines(create_ics_header(calname=calname, version=version, comments=comments)) + "\r\n")

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
                end=phase.end,  # exclusive
                summary=phase.name,
                description=f"{phase.emoji} — {phase.name}",
                emoji=phase.emoji,
                all_day=True,
            )
        )

    write_events_to_ics(
        events,
        filename,
        calname=CALNAME_PHASES,
        sort_by_start=True,
    )


def write_ebi48_layer(target_path: str | Path, year: int, alignment: str) -> None:
    """
    Write the EBI48 symbolic emoji clock as an .ics file: the same 48 events
    every day of the aligned year.

    - 48 timed events, one per half-hour slot, 25 minutes long, starting at
      HH:05 or HH:35 UTC on the alignment's anchor date for the year.
    - Each repeats daily: RRULE:FREQ=DAILY;UNTIL=<next anchor minus one second>.
      No COUNT, so the repeat limit some calendar apps impose never applies.
    - One all-day 🗝️ EBI48 Glyph Key event on the anchor date.

    EBI48 is UTC-fixed. It should not shift with local time.
    """
    anchor = get_year_start_date(year, alignment)
    next_anchor = get_year_start_date(year + 1, alignment)
    until = (next_anchor - datetime.timedelta(seconds=1)).strftime("%Y%m%dT%H%M%SZ")
    rule = f"FREQ=DAILY;UNTIL={until}"

    comments = [
        "EBI48 is a deterministic and symbolic emoji time layer.",
        "It repeats every day and does not shift with local time.",
        f"See: {EBI48_URL}",
    ]

    events: list[Event] = []

    # All-day glyph key marker
    events.append(
        Event(
            start=anchor,
            end=anchor + datetime.timedelta(days=1),
            summary="EBI48 Glyph Key",
            description="Symbolic marker: this calendar encodes canonical EBI48 slot glyphs (UTC-fixed).",
            emoji="🗝️",
            all_day=True,
            uid=generate_uid(dt=anchor, label="glyph-key", namespace="ebi48"),
        )
    )

    for hour in range(24):
        for minute in (5, 35):
            start = anchor.replace(hour=hour, minute=minute, second=0, microsecond=0)
            end = start + datetime.timedelta(minutes=25)
            emoji, label = get_emoji_for_time(start)

            description = (
                f"{emoji} {label} — Canonical EBI48 time at {hour:02d}:{minute:02d} UTC\\n"
                "This slot is part of the EBI48 symbolic clock.\\n"
                "🕒 UTC only — times do not shift with local time.\\n"
                f"{EBI48_URL}"
            )

            events.append(
                Event(
                    start=start,
                    end=end,
                    summary=label,
                    description=description,
                    emoji=emoji,
                    recurrence=rule,
                    uid=generate_uid(dt=start, label=f"{emoji} {label}", namespace="ebi48"),
                )
            )

    write_events_to_ics(
        events,
        target_path,
        calname=CALNAME_EBI48,
        comments=comments,
        sort_by_start=True,
    )
