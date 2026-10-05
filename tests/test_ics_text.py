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
    event = generate_focus_blocks_for_week(span, label="Semester A (Seed)", phase_emoji="🌱")[0]

    assert "\n" in event.description and "\\" not in event.description  # builders use real newlines
    (line,) = [x for x in event.to_ics() if x.startswith("DESCRIPTION:")]
    assert line.count(r"\n") == 2
    assert r"\\" not in line


# -----------------------------------------------------------------------------
# Control characters are rejected (v0.1.3)
# -----------------------------------------------------------------------------

ALLOWED_CONTROL_CODES = {0x09, 0x0A, 0x0D}  # TAB, LF, CR (LF and CR become the \n escape)
FORBIDDEN_CODES = [c for c in range(0x20) if c not in ALLOWED_CONTROL_CODES] + [0x7F]


@pytest.mark.parametrize("code", FORBIDDEN_CODES, ids=[f"U+{c:04X}" for c in FORBIDDEN_CODES])
def test_each_forbidden_control_character_is_rejected_and_named(code):
    char = chr(code)
    for value in (char, f"before{char}after", f"{char}at the start", f"at the end{char}"):
        with pytest.raises(ValueError, match=f"U\\+{code:04X}"):
            escape_ics_text(value)


def test_the_rejected_ranges_are_exactly_c0_minus_tab_cr_lf_plus_delete():
    assert FORBIDDEN_CODES[0] == 0x00 and FORBIDDEN_CODES[-1] == 0x7F
    rejected = set()
    for code in range(0x100):
        try:
            escape_ics_text("x" + chr(code) + "y")
        except ValueError:
            rejected.add(code)
    assert rejected == set(FORBIDDEN_CODES)  # in particular nothing above U+007F, and not U+0080-U+009F


def test_tab_is_allowed_and_left_as_it_is():
    assert escape_ics_text("a\tb") == "a\tb"
    assert escape_ics_text("\t") == "\t"
    assert escape_ics_text("tab\there\r\nand a newline") == "tab\there" + r"\n" + "and a newline"


def test_cr_and_lf_are_still_escaped_not_rejected():
    assert escape_ics_text("a\nb\rc\r\nd") == r"a\nb\nc\nd"


@pytest.mark.parametrize("char", ["\x80", "\x85", "\x9f", " ", " ", " ", "🦢", "é"])
def test_other_characters_pass_through(char):
    assert escape_ics_text(f"a{char}b") == f"a{char}b"


def test_the_message_names_the_code_point_and_shows_the_value():
    with pytest.raises(ValueError) as excinfo:
        escape_ics_text("ring the bell\x07 please")
    message = str(excinfo.value)
    assert "U+0007" in message and "ring the bell" in message and "RFC 5545" in message


def test_a_long_value_is_shortened_in_the_message():
    with pytest.raises(ValueError) as excinfo:
        escape_ics_text("x" * 500 + "\x00")
    message = str(excinfo.value)
    assert "U+0000" in message and "..." in message and "x" * 500 not in message


@pytest.mark.parametrize("bad", ["\x07", "\x00", "\x1b[31m", "\x7f"])
def test_every_text_property_rejects_control_characters(tmp_path, bad):
    path = tmp_path / "x.ics"
    with pytest.raises(ValueError, match="U\\+"):
        Event(start=START, summary=f"a{bad}b").to_ics()
    with pytest.raises(ValueError, match="U\\+"):
        Event(start=START, summary="s", description=f"a{bad}b").to_ics()
    with pytest.raises(ValueError, match="U\\+"):
        Event(start=START, summary="s", emoji=f"x{bad}").to_ics()
    with pytest.raises(ValueError, match="U\\+"):
        create_ics_header(calname=f"a{bad}b")
    with pytest.raises(ValueError, match="U\\+"):
        create_ics_header(comments=[f"a{bad}b"])

    # through the writer: the bad event surfaces as a render error, and no file is left behind
    with pytest.raises(ValueError, match="render event"):
        write_events_to_ics([Event(start=START, summary=f"a{bad}b")], path)
    with pytest.raises(ValueError, match="U\\+"):
        write_events_to_ics([Event(start=START, summary="fine")], path, calname=f"a{bad}b")
    assert not path.exists()


def test_calmojis_own_generated_text_never_contains_a_control_character(tmp_path):
    """Every file a run writes (with every optional layer) contains only allowed characters."""
    from calmoji.cli import main

    for alignment in ("academic", "calendar"):
        main(
            [
                "--year=2028",
                f"--calendar-alignment={alignment}",
                f"--output-dir={tmp_path / alignment}",
                "--include-oceania",
            ]
        )

    checked = 0
    for path in sorted(tmp_path.rglob("*.ics")):
        text = path.read_bytes().decode("utf-8")
        for char in text:
            code = ord(char)
            allowed = char in "\r\n" or char == "\t" or (code >= 0x20 and code != 0x7F)
            assert allowed, f"{path.name} contains U+{code:04X}"
        checked += 1
    assert checked > 50
