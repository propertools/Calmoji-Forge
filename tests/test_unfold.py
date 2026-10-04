# tests/test_unfold.py
"""unfold_ics_lines splits only where iCalendar does (CRLF, or a bare LF), then unfolds (RFC 5545 §3.1)."""

from __future__ import annotations

import datetime

import pytest

from calmoji.ics_writer import fold_ics_line, fold_lines, unfold_ics_lines, write_events_to_ics
from calmoji.types import Event
from tests.ics_helpers import read_events

UTC = datetime.timezone.utc

# Everything str.splitlines() treats as a line break that iCalendar does not.
NOT_LINE_BREAKS = [" ", " ", "\x85", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e"]


# -----------------------------------------------------------------------------
# What is not a line break
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("char", NOT_LINE_BREAKS)
def test_a_character_python_splits_on_but_icalendar_doesnt_stays_inside_its_line(char):
    line = f"DESCRIPTION:before{char}after"
    assert line.splitlines() != [line]  # the old implementation would have broken it in two
    assert unfold_ics_lines(line + "\r\n") == [line]
    assert unfold_ics_lines(line + "\n") == [line]
    assert unfold_ics_lines(line) == [line]


def test_a_value_with_u2028_and_x85_survives_a_fold_and_unfold_round_trip():
    value = "line one line two\x85line three end " + "x" * 200 + " " + "y" * 200
    line = f"DESCRIPTION:{value}"

    folded = fold_ics_line(line)
    assert "\r\n " in folded  # it really was folded, several times

    assert unfold_ics_lines(folded) == [line]
    assert unfold_ics_lines(fold_lines([line, "SUMMARY:next"]) + "\r\n") == [line, "SUMMARY:next"]


def test_a_description_with_those_characters_round_trips_through_a_written_file(tmp_path):
    description = "a b\x85c d"
    path = tmp_path / "e.ics"
    write_events_to_ics(
        [Event(start=datetime.datetime(2027, 3, 1, 9, tzinfo=UTC), summary="s", description=description)], path
    )

    (event,) = read_events(path)

    assert event["DESCRIPTION"] == description  # untouched: not escaped (not a control character), not split


def test_a_bare_carriage_return_is_not_a_line_break():
    assert unfold_ics_lines("A:one\rtwo\r\nB:x\r\n") == ["A:one\rtwo", "B:x"]


# -----------------------------------------------------------------------------
# CRLF and LF
# -----------------------------------------------------------------------------

FOLDED = [
    "BEGIN:VEVENT",
    "SUMMARY:a very long summary that is",
    "  folded across lines",
    "\tand with a tab",
    "END:VEVENT",
]
UNFOLDED = ["BEGIN:VEVENT", "SUMMARY:a very long summary that is folded across lines" + "and with a tab", "END:VEVENT"]


def test_crlf_and_lf_input_unfold_the_same_way():
    assert unfold_ics_lines("\r\n".join(FOLDED) + "\r\n") == UNFOLDED
    assert unfold_ics_lines("\n".join(FOLDED) + "\n") == UNFOLDED
    assert unfold_ics_lines("\r\n".join(FOLDED)) == UNFOLDED  # no final newline
    assert unfold_ics_lines("\n".join(FOLDED)) == UNFOLDED


def test_mixed_crlf_and_lf_in_one_file():
    assert unfold_ics_lines("A:1\r\nB:2\nC:3\r\n") == ["A:1", "B:2", "C:3"]


def test_a_continuation_may_start_with_a_space_or_a_tab_and_exactly_one_character_is_dropped():
    assert unfold_ics_lines("A:ab\r\n cd\r\n") == ["A:abcd"]
    assert unfold_ics_lines("A:ab\r\n\tcd\r\n") == ["A:abcd"]
    assert unfold_ics_lines("A:ab\r\n  cd\r\n") == ["A:ab cd"]  # the second space belongs to the value
    assert unfold_ics_lines("A:ab\r\n \tcd\r\n") == ["A:ab\tcd"]


def test_the_real_folder_and_unfolder_agree_on_a_long_line_of_emoji():
    line = "SUMMARY:" + "🦢 Swan Face; " * 30
    assert unfold_ics_lines(fold_ics_line(line)) == [line]


# -----------------------------------------------------------------------------
# Edges that must not change
# -----------------------------------------------------------------------------


def test_empty_input_and_trailing_newlines():
    assert unfold_ics_lines("") == []
    assert unfold_ics_lines("\r\n") == [""]
    assert unfold_ics_lines("A:1\r\n") == ["A:1"]
    assert unfold_ics_lines("A:1\r\n\r\n") == ["A:1", ""]  # interior and trailing blank lines are kept as blank lines
    assert unfold_ics_lines("A:1\r\n\r\nB:2") == ["A:1", "", "B:2"]


def test_a_continuation_with_nothing_before_it_is_malformed():
    with pytest.raises(ValueError, match="continuation line on line 1"):
        unfold_ics_lines(" orphan\r\n")
    with pytest.raises(ValueError, match="continuation line on line 1"):
        unfold_ics_lines("\torphan")


def test_a_blank_line_ends_what_a_following_continuation_may_join():
    # A blank line is a line of its own, so a continuation after it joins the blank line, not the one before.
    assert unfold_ics_lines("A:1\r\n\r\n x\r\n") == ["A:1", "x"]
