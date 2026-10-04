# tests/test_2039.py

from __future__ import annotations

import datetime

from calmoji.calendar_phases import get_semester_phases
from calmoji.generator import get_all_events
from calmoji.ics_writer import create_ics_footer, create_ics_header, fold_lines

UTC = datetime.timezone.utc


def _extract_ics_datetime_value(line: str) -> str | None:
    if not (line.startswith("DTSTART") or line.startswith("DTEND")):
        return None
    if ":" not in line:
        return None
    return line.split(":", 1)[1].strip()


def _year_from_value(val: str) -> int:
    return int(val[0:4])


def _is_exclusive_year_boundary(val: str) -> bool:
    return val in {"20400101", "20400101T000000Z"}


def _render_year_to_ics_text(year: int, alignment: str = "calendar") -> str:
    phases = get_semester_phases(year, alignment)
    events = get_all_events(phases)

    year_start = datetime.datetime(year, 1, 1, tzinfo=UTC)
    year_end = datetime.datetime(year + 1, 1, 1, tzinfo=UTC)

    # Clip: only serialize events whose DTSTART is inside the target year
    events = [e for e in events if year_start <= e.start < year_end]

    lines: list[str] = []
    lines.extend(create_ics_header(calname="🧿 calmoji test", version=str(year)))
    for e in events:
        lines.extend(e.to_ics())
    lines.extend(create_ics_footer())

    return fold_lines(lines) + "\r\n"


def test_only_2039_events_appear_in_calendar_output():
    output = _render_year_to_ics_text(2039, alignment="calendar")

    dtstarts: list[str] = []
    dtends: list[str] = []

    for line in output.splitlines():
        if line.startswith("DTSTART"):
            v = _extract_ics_datetime_value(line)
            if v:
                dtstarts.append(v)
        elif line.startswith("DTEND"):
            v = _extract_ics_datetime_value(line)
            if v:
                dtends.append(v)

    assert dtstarts, "No DTSTART lines found; calendar output looks empty or malformed."
    assert dtends, "No DTEND lines found; calendar output looks empty or malformed."
    assert len(dtstarts) == len(dtends), "Mismatched DTSTART/DTEND counts."

    bad_starts = [v for v in dtstarts if _year_from_value(v) != 2039]
    assert not bad_starts, f"Found DTSTART values outside 2039: {bad_starts[:10]}"

    bad_ends = [v for v in dtends if (_year_from_value(v) != 2039 and not _is_exclusive_year_boundary(v))]
    assert not bad_ends, f"Found DTEND values outside allowed range: {bad_ends[:10]}"
