# tests/test_ebi48_layer.py
"""The EBI48 layer: the same 48 events every day of the aligned year."""

from __future__ import annotations

import datetime
import re
from pathlib import Path

import pytest

import calmoji
from calmoji.calendar_config import ALIGNMENT_MODES, get_year_start_date
from calmoji.cli import main
from calmoji.constants import CALNAME_EBI48, EBI48_URL
from calmoji.ebi48 import EBI48_CLOCK
from calmoji.ics_writer import write_ebi48_layer
from tests.ics_helpers import end_of, header_lines, is_all_day, read_events, start_of

UTC = datetime.timezone.utc

# 2027 academic spans 29 Feb 2028; 2028 calendar is a leap year; 2029 is ordinary.
CASES = [("academic", 2027), ("academic", 2028), ("calendar", 2028), ("calendar", 2029)]
RULE_RE = re.compile(r"^FREQ=DAILY;UNTIL=(\d{8}T\d{6}Z)$")


@pytest.fixture(params=CASES, ids=[f"{a}-{y}" for a, y in CASES])
def layer(request, tmp_path):
    alignment, year = request.param
    path = tmp_path / "ebi48.ics"
    write_ebi48_layer(path, year, alignment)
    return alignment, year, path, read_events(path)


def test_exactly_48_events_all_timed_and_all_recurring_daily(layer):
    _, _, _, events = layer
    assert len(events) == 48
    assert not any(is_all_day(e) for e in events)
    assert all(RULE_RE.match(e["RRULE"]) for e in events)


def test_timed_events_start_on_the_anchor_date_at_5_and_35_past(layer):
    alignment, year, _, events = layer
    anchor = get_year_start_date(year, alignment)
    timed = sorted((e for e in events if not is_all_day(e)), key=start_of)

    expected_starts = [anchor.replace(hour=h, minute=m) for h in range(24) for m in (5, 35)]
    assert [start_of(e) for e in timed] == expected_starts
    for e in timed:
        assert end_of(e) - start_of(e) == datetime.timedelta(minutes=25)
        assert re.fullmatch(r"\d{8}T\d{4}00Z", e["DTSTART"])


def test_every_rule_is_exactly_daily_until_just_before_the_next_anchor(layer):
    alignment, year, _, events = layer
    next_anchor = get_year_start_date(year + 1, alignment)

    for e in events:
        match = RULE_RE.match(e["RRULE"])
        assert match, e["RRULE"]
        until = datetime.datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
        assert until == next_anchor - datetime.timedelta(seconds=1)
        assert until < next_anchor


def test_the_clock_covers_every_day_of_the_year(layer):
    # Each rule's first occurrence is the anchor and its last the day before the next anchor.
    alignment, year, _, events = layer
    anchor = get_year_start_date(year, alignment)
    next_anchor = get_year_start_date(year + 1, alignment)
    days = (next_anchor - anchor).days
    assert days in (365, 366)

    for e in (e for e in events if not is_all_day(e)):
        until = datetime.datetime.strptime(RULE_RE.match(e["RRULE"]).group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
        first = start_of(e)
        assert until.time() > first.time()  # so the last day's occurrence is not cut off by UNTIL
        assert (until - first).days + 1 == days


def test_summary_shows_the_emoji_once_and_matches_the_table(layer):
    _, _, _, events = layer
    by_start = {(start_of(e).hour, start_of(e).minute): e for e in events if not is_all_day(e)}
    for slot, (emoji, name) in EBI48_CLOCK.items():
        hour, minute = divmod(slot, 2)
        event = by_start[(hour, 5 if slot % 2 == 0 else 35)]
        assert event["SUMMARY"] == f"{emoji} {name}"
        assert event["SUMMARY"].count(emoji) == 1


def test_there_is_no_glyph_key(layer):
    _, _, path, events = layer
    text = path.read_bytes().decode("utf-8").replace("\r\n ", "")
    assert "Glyph Key" not in text and "\U0001f5dd" not in text
    assert not any("Glyph" in e["SUMMARY"] for e in events)


def test_calendar_name_and_reference_link(layer):
    _, _, path, events = layer
    header = header_lines(path)
    assert f"X-WR-CALNAME:{CALNAME_EBI48}" in header
    assert CALNAME_EBI48 == "🧿 Emoji Clock"
    text = path.read_bytes().decode("utf-8").replace("\r\n ", "")
    assert "ebi48.org" not in text
    assert EBI48_URL in text


def test_uids_are_unique(layer):
    _, _, _, events = layer
    uids = [e["UID"] for e in events]
    assert len(uids) == len(set(uids))


@pytest.mark.parametrize("alignment", sorted(ALIGNMENT_MODES))
def test_no_generated_file_contains_count(tmp_path, alignment):
    main(["--year=2028", f"--calendar-alignment={alignment}", f"--output-dir={tmp_path}", "--include-oceania"])
    files = list(tmp_path.rglob("*.ics"))
    assert files
    for path in files:
        assert "COUNT=" not in path.read_bytes().decode("utf-8").replace("\r\n ", ""), path.name


def test_the_package_never_uses_count():
    for source in Path(calmoji.__file__).parent.glob("*.py"):
        assert "COUNT=" not in source.read_text(encoding="utf-8"), source.name


def test_the_old_options_are_gone(tmp_path):
    with pytest.raises(TypeError):
        write_ebi48_layer(tmp_path / "x.ics", 2027, "academic", recurring=True)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        write_ebi48_layer(tmp_path / "x.ics", 2027, "academic", expanded=True)  # type: ignore[call-arg]
