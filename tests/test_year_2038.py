# tests/test_year_2038.py
"""
Every fact in the README's "Testing for the year-2038 problem" section, checked against the files
calmoji really generates (so the text can't drift from the output).
"""

from __future__ import annotations

import datetime
import re
from pathlib import Path
from typing import Dict, List

import pytest

from calmoji.cli import main
from calmoji.ebi48 import EBI48_CLOCK
from calmoji.focus_blocks_config import FOCUS_BLOCKS
from tests.ics_helpers import end_of, read_events, start_of

UTC = datetime.timezone.utc
ROOT = Path(__file__).resolve().parent.parent

# The second a signed 32-bit time_t can no longer count past.
LAST_32_BIT_SECOND = datetime.datetime(1970, 1, 1, tzinfo=UTC) + datetime.timedelta(seconds=2**31 - 1)


@pytest.fixture(scope="module")
def bundle(tmp_path_factory) -> Path:
    """The four year folders the section talks about, laid out like the release bundle."""
    root = tmp_path_factory.mktemp("year2038")
    for year, alignment in ((2037, "academic"), (2037, "calendar"), (2038, "academic"), (2038, "calendar")):
        main(
            [
                f"--year={year}",
                f"--calendar-alignment={alignment}",
                f"--output-dir={root / str(year) / alignment}",
                "--no-meetings",
            ]
        )
    return root


def test_the_32_bit_limit_is_03_14_07_utc_on_19_january_2038():
    assert LAST_32_BIT_SECOND == datetime.datetime(2038, 1, 19, 3, 14, 7, tzinfo=UTC)


def test_january_2038_is_in_the_2037_academic_and_2038_calendar_folders_only(bundle):
    found = sorted(p.relative_to(bundle).as_posix() for p in bundle.glob("*/*/focus/focus_2038-01.ics"))
    assert found == ["2037/academic/focus/focus_2038-01.ics", "2038/calendar/focus/focus_2038-01.ics"]


def test_the_two_files_the_readme_names_exist(bundle):
    assert (bundle / "2038/calendar/focus/focus_2038-01.ics").is_file()
    assert (bundle / "2037/academic/emoji_clock_2037.ics").is_file()


def test_focus_block_2_spans_the_exact_second(bundle):
    block_2 = FOCUS_BLOCKS[1]
    assert block_2[0] == 2 and block_2[1:5] == (2, 0, 3, 36)  # 02:00-03:36 UTC
    block_2_emoji = block_2[5]

    for rel in ("2038/calendar/focus/focus_2038-01.ics", "2037/academic/focus/focus_2038-01.ics"):
        events = read_events(bundle / rel)
        spanning = [e for e in events if start_of(e) <= LAST_32_BIT_SECOND < end_of(e)]
        assert len(spanning) == 1, rel  # exactly one block spans it
        (block,) = spanning
        assert block["SUMMARY"].startswith(f"{block_2_emoji} Focus Block 2 — ")
        assert (start_of(block).time(), end_of(block).time()) == (datetime.time(2, 0), datetime.time(3, 36))
        assert start_of(block).date() == datetime.date(2038, 1, 19)


def test_the_readme_names_the_right_emoji_for_focus_block_2():
    readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    emoji = FOCUS_BLOCKS[1][5]
    assert f"{emoji} Focus Block 2 (02:00–03:36 UTC)" in readme
    assert FOCUS_BLOCKS[0][5] != emoji  # not block 1's emoji, which is what the first draft used


def test_the_raccoon_slot_spans_the_exact_second(bundle):
    assert EBI48_CLOCK[6] == ("🦝", "Raccoon Face")  # slot 6 = 03:05 UTC
    for rel in ("2037/academic/emoji_clock_2037.ics", "2038/calendar/emoji_clock_2038.ics"):
        events = read_events(bundle / rel)
        (raccoon,) = [e for e in events if e["SUMMARY"] == "🦝 Raccoon Face"]
        assert (start_of(raccoon).time(), end_of(raccoon).time()) == (datetime.time(3, 5), datetime.time(3, 30))
        assert start_of(raccoon).time() <= LAST_32_BIT_SECOND.time() < end_of(raccoon).time()
        # it recurs daily, so it is there on 19 January 2038: that date is inside its repeat range
        until = re.fullmatch(r"FREQ=DAILY;UNTIL=(\d{8})T235959Z", raccoon["RRULE"])
        assert until
        first = start_of(raccoon).date()
        last = datetime.datetime.strptime(until.group(1), "%Y%m%d").date()
        assert first <= LAST_32_BIT_SECOND.date() <= last


def test_the_2037_academic_emoji_clock_repeats_on_into_august_2038(bundle):
    events: List[Dict[str, str]] = read_events(bundle / "2037/academic/emoji_clock_2037.ics")
    assert len(events) == 48
    for e in events:
        assert e["RRULE"] == "FREQ=DAILY;UNTIL=20380831T235959Z"
    assert start_of(events[0]).date() == datetime.date(2037, 9, 1)


def test_nothing_else_in_the_four_folders_is_in_january_2038(bundle):
    # 2038 academic starts in September 2038 and 2037 calendar ends in December 2037.
    assert not list((bundle / "2038" / "academic" / "focus").glob("focus_2038-01.ics"))
    assert not list((bundle / "2037" / "calendar" / "focus").glob("focus_2038-*.ics"))
    assert sorted(p.name for p in (bundle / "2038" / "academic" / "focus").iterdir())[0] == "focus_2038-09.ics"
