# tests/test_monthly.py
"""Unit tests for calmoji.monthly: bucketing events by UTC month."""

from __future__ import annotations

import datetime

from calmoji.constants import CALNAME_FOCUS
from calmoji.monthly import MonthRow, bucket_by_month, month_key, month_rows, write_monthly_files
from calmoji.types import Event
from tests.ics_helpers import header_lines, read_events

UTC = datetime.timezone.utc


def event(year, month, day, hour=0, minute=0, name="e", all_day=False) -> Event:
    return Event(start=datetime.datetime(year, month, day, hour, minute, tzinfo=UTC), summary=name, all_day=all_day)


def test_month_key():
    assert month_key(datetime.datetime(2027, 3, 9, tzinfo=UTC)) == "2027-03"
    assert month_key(datetime.datetime(987, 11, 1, tzinfo=UTC)) == "0987-11"


def test_events_are_bucketed_by_the_utc_month_of_their_start():
    events = [
        event(2027, 1, 31, 23, 35, "late january"),
        event(2027, 2, 1, 0, 5, "early february"),
        event(2027, 2, 28, 12, name="mid february"),
    ]

    buckets = bucket_by_month(events)

    assert list(buckets) == ["2027-01", "2027-02"]
    assert [e.summary for e in buckets["2027-01"]] == ["late january"]
    assert [e.summary for e in buckets["2027-02"]] == ["early february", "mid february"]


def test_the_boundary_belongs_to_the_later_month():
    last_second_of_january = Event(start=datetime.datetime(2027, 1, 31, 23, 59, 59, tzinfo=UTC), summary="a")
    first_of_february = event(2027, 2, 1, 0, 0, "b")
    buckets = bucket_by_month([first_of_february, last_second_of_january])
    assert {k: [e.summary for e in v] for k, v in buckets.items()} == {"2027-01": ["a"], "2027-02": ["b"]}


def test_an_all_day_event_goes_by_its_date():
    key = event(2027, 11, 1, name="key", all_day=True)
    assert list(bucket_by_month([key])) == ["2027-11"]


def test_months_are_sorted_and_events_within_a_month_are_sorted_stably():
    a = event(2027, 3, 2, 10, name="a")
    b = event(2027, 3, 2, 10, name="b")  # same start as a: input order is kept
    c = event(2027, 3, 1, 10, name="c")
    d = event(2026, 12, 31, 10, name="d")

    buckets = bucket_by_month([a, b, d, c])

    assert list(buckets) == ["2026-12", "2027-03"]
    assert [e.summary for e in buckets["2027-03"]] == ["c", "a", "b"]


def test_empty_input_gives_no_buckets_and_no_files(tmp_path):
    assert bucket_by_month([]) == {}
    assert write_monthly_files([], tmp_path / "focus", "focus", CALNAME_FOCUS) == []
    assert not (tmp_path / "focus").exists()


def test_only_months_with_events_are_written(tmp_path):
    events = [event(2027, 1, 5), event(2027, 4, 7), event(2027, 4, 9)]  # no February or March

    written = write_monthly_files(events, tmp_path / "focus", "focus", CALNAME_FOCUS)

    assert [p.name for p in written] == ["focus_2027-01.ics", "focus_2027-04.ics"]
    assert sorted(p.name for p in (tmp_path / "focus").iterdir()) == ["focus_2027-01.ics", "focus_2027-04.ics"]
    assert [len(read_events(p)) for p in written] == [1, 2]
    assert f"X-WR-CALNAME:{CALNAME_FOCUS}" in header_lines(written[0])


def test_no_event_is_written_twice(tmp_path):
    events = [event(2027, m, d, name=f"{m}-{d}") for m in (1, 2, 3) for d in (1, 15, 28)]

    written = write_monthly_files(events, tmp_path, "m", "name")

    uids = [e["UID"] for p in written for e in read_events(p)]
    assert len(uids) == len(events) == len(set(uids))


def test_month_rows_count_focus_blocks_and_meeting_slots():
    focus = [event(2027, 9, 1, name="block"), event(2027, 9, 2, name="block 2")]
    meetings = [event(2027, 9, 7, name="m1"), event(2027, 10, 1, name="m2")]

    assert month_rows(focus, meetings) == [MonthRow("2027-09", 2, 1), MonthRow("2027-10", 0, 1)]
    assert month_rows([], []) == []
