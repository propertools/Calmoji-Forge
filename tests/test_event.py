# tests/test_event.py
"""Event end rules: timed events must end after they start; all-day events follow one documented rule."""

from __future__ import annotations

import datetime

import pytest

from calmoji.types import Event

UTC = datetime.timezone.utc


def dt(year, month, day, hour=0, minute=0, second=0, microsecond=0):
    return datetime.datetime(year, month, day, hour, minute, second, microsecond, tzinfo=UTC)


def lines(event: Event):
    return {
        line.split(":", 1)[0]: line.split(":", 1)[1] for line in event.to_ics() if line.startswith(("DTSTART", "DTEND"))
    }


# -----------------------------------------------------------------------------
# Timed events
# -----------------------------------------------------------------------------


def test_a_timed_event_defaults_to_one_hour():
    event = Event(start=dt(2027, 3, 1, 9), summary="x")
    assert event.end == dt(2027, 3, 1, 10)


def test_a_timed_event_may_end_after_it_starts():
    event = Event(start=dt(2027, 3, 1, 9), end=dt(2027, 3, 1, 9, 0, 1), summary="x")
    assert event.end == dt(2027, 3, 1, 9, 0, 1)


def test_a_timed_event_that_ends_when_it_starts_raises():
    with pytest.raises(ValueError, match="must be after its start"):
        Event(start=dt(2027, 3, 1, 9), end=dt(2027, 3, 1, 9), summary="x")


@pytest.mark.parametrize("end", [dt(2027, 3, 1, 8, 59, 59), dt(2027, 3, 1, 8), dt(2027, 2, 28, 9), dt(2026, 3, 1, 9)])
def test_a_timed_event_that_ends_before_it_starts_raises(end):
    with pytest.raises(ValueError, match="must be after its start"):
        Event(start=dt(2027, 3, 1, 9), end=end, summary="x")


def test_timed_events_keep_their_dtstart_and_dtend():
    event = Event(start=dt(2027, 3, 1, 9, 5), end=dt(2027, 3, 1, 9, 30), summary="x")
    assert lines(event) == {"DTSTART": "20270301T090500Z", "DTEND": "20270301T093000Z"}


# -----------------------------------------------------------------------------
# All-day events: one rule
# -----------------------------------------------------------------------------


def test_an_all_day_event_defaults_to_one_day():
    event = Event(start=dt(2027, 3, 1), summary="x", all_day=True)
    assert (event.start, event.end) == (dt(2027, 3, 1), dt(2027, 3, 2))
    assert lines(event) == {"DTSTART;VALUE=DATE": "20270301", "DTEND;VALUE=DATE": "20270302"}


def test_an_all_day_start_is_floored_to_midnight():
    event = Event(start=dt(2027, 3, 1, 15, 30), summary="x", all_day=True)
    assert event.start == dt(2027, 3, 1)


def test_an_end_at_midnight_is_exclusive():
    event = Event(start=dt(2027, 3, 1), end=dt(2027, 3, 3), summary="x", all_day=True)
    assert event.end == dt(2027, 3, 3)  # covers the 1st and the 2nd
    assert lines(event)["DTEND;VALUE=DATE"] == "20270303"


def test_an_end_at_the_next_midnight_is_one_day():
    event = Event(start=dt(2027, 3, 1), end=dt(2027, 3, 2), summary="x", all_day=True)
    assert event.end == dt(2027, 3, 2)


@pytest.mark.parametrize("end", [dt(2027, 3, 1), dt(2027, 2, 28), dt(2026, 3, 1)])
def test_a_midnight_end_on_or_before_the_start_date_raises(end):
    with pytest.raises(ValueError, match="must be after its start"):
        Event(start=dt(2027, 3, 1), end=end, summary="x", all_day=True)


def test_an_end_with_a_time_of_day_means_through_that_date():
    event = Event(start=dt(2027, 3, 1), end=dt(2027, 3, 3, 8), summary="x", all_day=True)
    assert event.end == dt(2027, 3, 4)  # inclusive of the 3rd


@pytest.mark.parametrize(
    "end",
    [dt(2027, 3, 1, 8), dt(2027, 3, 1, 23), dt(2027, 3, 1, 23, 59, 59, 999999), dt(2027, 3, 1, 0, 0, 0, 1)],
)
def test_an_end_with_a_time_of_day_on_the_start_date_is_a_one_day_event(end):
    event = Event(start=dt(2027, 3, 1), end=end, summary="x", all_day=True)
    assert (event.start, event.end) == (dt(2027, 3, 1), dt(2027, 3, 2))


def test_eight_to_twenty_three_on_one_date_is_a_one_day_all_day_event():
    event = Event(start=dt(2027, 3, 1, 8), end=dt(2027, 3, 1, 23), summary="x", all_day=True)
    assert (event.start, event.end) == (dt(2027, 3, 1), dt(2027, 3, 2))
    assert lines(event) == {"DTSTART;VALUE=DATE": "20270301", "DTEND;VALUE=DATE": "20270302"}


def test_an_end_with_a_time_of_day_before_the_start_date_raises():
    with pytest.raises(ValueError, match="before its start date"):
        Event(start=dt(2027, 3, 2), end=dt(2027, 3, 1, 23, 59), summary="x", all_day=True)


def test_timed_end_earlier_in_the_day_than_the_start_is_fine_for_all_day():
    # The start's time of day is discarded, so only the dates matter.
    event = Event(start=dt(2027, 3, 1, 22), end=dt(2027, 3, 1, 6), summary="x", all_day=True)
    assert (event.start, event.end) == (dt(2027, 3, 1), dt(2027, 3, 2))


# -----------------------------------------------------------------------------
# Unchanged behaviour
# -----------------------------------------------------------------------------


def test_events_must_be_utc():
    other = datetime.timezone(datetime.timedelta(hours=2))
    with pytest.raises(ValueError, match="UTC"):
        Event(start=datetime.datetime(2027, 3, 1, tzinfo=other), summary="x")
    with pytest.raises(ValueError, match="UTC"):
        Event(start=dt(2027, 3, 1), end=datetime.datetime(2027, 3, 2, tzinfo=other), summary="x")
    assert Event(start=datetime.datetime(2027, 3, 1), summary="x").start == dt(2027, 3, 1)  # naive means UTC


def test_the_uid_does_not_depend_on_the_end():
    a = Event(start=dt(2027, 3, 1), summary="x", all_day=True)
    b = Event(start=dt(2027, 3, 1), end=dt(2027, 3, 9), summary="x", all_day=True)
    assert a.uid == b.uid


def test_the_docstring_states_the_rules():
    doc = Event.__doc__ or ""
    for phrase in ("end <= start", "EXCLUSIVE midnight", "through that date", "08:00-23:00 on one date"):
        assert phrase in doc
