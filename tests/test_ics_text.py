# tests/test_ics_text.py
"""RFC 5545 §3.3.11 TEXT escaping: every TEXT property, adversarial values, no injection, folding intact."""

from __future__ import annotations

import datetime
import re
from pathlib import Path

import pytest

from calmoji.focus_blocks import generate_focus_blocks_for_week
from calmoji.ics_text import escape_ics_text
from calmoji.ics_writer import create_ics_header, fold_ics_line, fold_lines, unfold_ics_lines, write_events_to_ics
from calmoji.types import Event, PhaseWeekSpan

UTC = datetime.timezone.utc
START = datetime.datetime(2027, 3, 1, 9, 5, tzinfo=UTC)

# (raw value, what the file must contain after "PROPERTY:"). Raw strings (r"...") are literal:
# r"\;" is a backslash followed by a semicolon, and so on.
CASES = [
    ("plain", "plain"),
    ("back" + "\\" + "slash", r"back\\slash"),
    ("semi;colon", r"semi\;colon"),
    ("com,ma", r"com\,ma"),
    ("line\nfeed", r"line\nfeed"),
    ("carriage\rreturn", r"carriage\nreturn"),
    ("crlf\r\nbreak", r"crlf\nbreak"),
    ("lf\n\ncr\r\rcrlf\r\n", r"lf\n\ncr\n\ncrlf\n"),
    ("mixed " + "\\" + " ; , \n \r\n \r end", r"mixed \\ \; \, \n \n \n end"),
    ("already " + "\\" + "n escaped " + "\\" + "; looking", r"already \\n escaped \\\; looking"),
    ("trailing backslash " + "\\", r"trailing backslash \\"),
    ("emoji 🦢 — Swan, Face; ⛩️ 👨‍👩‍👧", r"emoji 🦢 — Swan\, Face\; ⛩️ 👨‍👩‍👧"),
    ("Hello\nATTENDEE:mailto:x@example.com", r"Hello\nATTENDEE:mailto:x@example.com"),
    ("Hello\r\nBEGIN:VEVENT\r\nEND:VEVENT", r"Hello\nBEGIN:VEVENT\nEND:VEVENT"),
    ("x y\x85z", "x y\x85z"),  # not iCalendar line breaks: left alone
]


@pytest.mark.parametrize(("raw", "escaped"), CASES)
def test_escape_ics_text(raw, escaped):
    assert escape_ics_text(raw) == escaped


def test_backslash_is_escaped_before_the_other_escapes():
    # If it weren't, the backslashes the escaper adds would be doubled.
    assert escape_ics_text(";") == r"\;"
    assert escape_ics_text(r"\;") == r"\\\;"
    assert escape_ics_text("\n") == r"\n"
    assert escape_ics_text(r"\n") == r"\\n"  # a literal backslash-n is two characters, both preserved


def unescape(text: str) -> str:
    """Test-only inverse (RFC 5545 §3.3.11) used to prove the escape round-trips."""
    return re.sub(r"\\(.)", lambda m: "\n" if m.group(1) in "nN" else m.group(1), text)


@pytest.mark.parametrize(("raw", "_"), CASES)
def test_escaping_round_trips(raw, _):
    assert unescape(escape_ics_text(raw)) == raw.replace("\r\n", "\n").replace("\r", "\n")


# -----------------------------------------------------------------------------
# What reaches the file, property by property
# -----------------------------------------------------------------------------

EVENT_PROPERTIES = {
    "BEGIN",
    "UID",
    "DTSTAMP",
    "SUMMARY",
    "DTSTART",
    "DTEND",
    "DESCRIPTION",
    "RRULE",
    "CLASS",
    "TRANSP",
    "END",
}
HEADER_PROPERTIES = {
    "BEGIN",
    "VERSION",
    "CALSCALE",
    "PRODID",
    "NAME",
    "X-WR-CALNAME",
    "X-WR-TIMEZONE",
    "METHOD",
    "COMMENT",
    "END",
}


def logical_lines(path: Path) -> list:
    """Split like an iCalendar parser does (CRLF only), then unfold."""
    raw = path.read_bytes().decode("utf-8")
    assert raw.endswith("\r\n")
    physical = raw[:-2].split("\r\n")
    assert all("\n" not in line and "\r" not in line for line in physical)
    unfolded: list = []
    for line in physical:
        if line.startswith(" "):
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    return unfolded


def property_names(lines) -> set:
    return {re.split(r"[:;]", line, maxsplit=1)[0] for line in lines}


@pytest.mark.parametrize(("raw", "escaped"), CASES)
def test_summary_and_description_are_escaped_in_the_file(tmp_path, raw, escaped):
    path = tmp_path / "e.ics"
    write_events_to_ics([Event(start=START, summary=raw, description=raw)], path)

    lines = logical_lines(path)
    assert f"SUMMARY:{escaped}" in lines
    assert f"DESCRIPTION:{escaped}" in lines
    # still exactly one VEVENT with exactly the properties calmoji writes: nothing was injected
    assert property_names(lines) - EVENT_PROPERTIES - HEADER_PROPERTIES == set()
    assert sum(1 for line in lines if line.startswith("SUMMARY:")) == 1
    assert sum(1 for line in lines if line == "BEGIN:VEVENT") == 1


@pytest.mark.parametrize(("raw", "escaped"), CASES)
def test_the_emoji_prefix_and_summary_are_escaped_together(tmp_path, raw, escaped):
    path = tmp_path / "e.ics"
    write_events_to_ics([Event(start=START, summary=raw, emoji="🦢")], path)
    assert f"SUMMARY:🦢 {escaped}" in logical_lines(path)


@pytest.mark.parametrize(("raw", "escaped"), CASES)
def test_calendar_name_and_comments_are_escaped_in_the_file(tmp_path, raw, escaped):
    path = tmp_path / "c.ics"
    write_events_to_ics([Event(start=START, summary="x")], path, calname=raw, comments=[raw, "second"])

    lines = logical_lines(path)
    # The calendar name has always been stripped of surrounding whitespace before use.
    name = escaped if raw == raw.strip() else escape_ics_text(raw.strip())
    assert f"NAME:{name}" in lines
    assert f"X-WR-CALNAME:{name}" in lines
    assert f"COMMENT:{escaped}" in lines  # comments are written as given
    assert "COMMENT:second" in lines
    assert property_names(lines) - EVENT_PROPERTIES - HEADER_PROPERTIES == set()
    assert sum(1 for line in lines if line == "BEGIN:VCALENDAR") == 1


def test_the_injection_case_from_the_review(tmp_path):
    path = tmp_path / "evil.ics"
    write_events_to_ics([Event(start=START, summary="Hello\nATTENDEE:mailto:x@example.com")], path)

    raw = path.read_bytes().decode("utf-8")
    assert not any(line.startswith("ATTENDEE") for line in raw.split("\r\n"))
    assert "SUMMARY:Hello" + r"\n" + "ATTENDEE:mailto:x@example.com\r\n" in raw


def test_header_lines_are_escaped_before_folding():
    lines = create_ics_header(calname="a;b,c\nd", comments=["x\r\ny"])
    assert r"NAME:a\;b\,c\nd" in lines
    assert r"X-WR-CALNAME:a\;b\,c\nd" in lines
    assert r"COMMENT:x\ny" in lines
    # constant, non-TEXT values are untouched
    assert "PRODID:-//Proper Tools SRL//calmoji//EN" in lines
    assert "X-WR-TIMEZONE:UTC" in lines


def test_non_text_properties_are_not_escaped():
    event = Event(start=START, summary="s", uid="abc-123@calmoji.local", recurrence="FREQ=DAILY;UNTIL=20271231T235959Z")
    lines = event.to_ics()
    assert "UID:abc-123@calmoji.local" in lines
    assert "RRULE:FREQ=DAILY;UNTIL=20271231T235959Z" in lines
    assert "DTSTART:20270301T090500Z" in lines


@pytest.mark.parametrize("bad", ["x\nATTENDEE:mailto:x@example.com", "x\rATTENDEE:y", "x\r\ny"])
def test_uid_and_rrule_cannot_carry_a_line_break(bad):
    with pytest.raises(ValueError, match="UID"):
        Event(start=START, summary="s", uid=bad).to_ics()
    with pytest.raises(ValueError, match="RRULE"):
        Event(start=START, summary="s", recurrence=bad).to_ics()


def test_a_bad_event_surfaces_through_the_writer(tmp_path):
    with pytest.raises(ValueError, match="render event"):
        write_events_to_ics([Event(start=START, summary="s", uid="a\nb")], tmp_path / "x.ics")
    assert not (tmp_path / "x.ics").exists()


# -----------------------------------------------------------------------------
# Folding still holds at 75 octets
# -----------------------------------------------------------------------------

LONG_VALUES = [
    ",;" + "\\" * 120,
    "🦢 Swan, Face; ⛩️\n" * 40,
    ("a,b;c" + "\\" + "d\r\n") * 60 + "🪿" * 80,
    "x" * 1000,
]


@pytest.mark.parametrize("value", LONG_VALUES)
def test_every_physical_line_stays_within_75_octets(tmp_path, value):
    path = tmp_path / "long.ics"
    write_events_to_ics(
        [Event(start=START, summary=value, description=value, emoji="🦢")],
        path,
        calname=value,
        comments=[value],
    )

    physical = path.read_bytes().split(b"\r\n")[:-1]
    assert physical
    assert max(len(line) for line in physical) <= 75
    assert all(line.decode("utf-8") for line in physical)  # no character cut in half

    # and unfolding gives back the escaped value
    lines = logical_lines(path)
    assert f"DESCRIPTION:{escape_ics_text(value)}" in lines
    assert f"SUMMARY:🦢 {escape_ics_text(value)}" in lines


def test_fold_does_not_care_where_it_splits_an_escape():
    line = "DESCRIPTION:" + escape_ics_text("a;" * 100)
    folded = fold_ics_line(line)
    assert all(len(part.encode("utf-8")) <= 75 for part in folded.split("\r\n"))
    assert unfold_ics_lines(folded) == [line]
    assert unfold_ics_lines(fold_lines([line, line])) == [line, line]


# -----------------------------------------------------------------------------
# calmoji's own builders use real newlines, so the escaper produces exactly one "\n"
# -----------------------------------------------------------------------------


def test_focus_block_descriptions_show_single_backslash_n_sequences():
    span = PhaseWeekSpan(start=datetime.datetime(2027, 3, 1, tzinfo=UTC), phase_name="p", week_index=0)
    event = generate_focus_blocks_for_week(span, label="Semester A (Seed)", phase_emoji="🌱")[1]

    assert "\n" in event.description and "\\" not in event.description  # builders use real newlines
    (line,) = [x for x in event.to_ics() if x.startswith("DESCRIPTION:")]
    assert line.count(r"\n") == 2
    assert r"\\" not in line
