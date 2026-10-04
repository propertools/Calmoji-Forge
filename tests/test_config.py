# tests/test_config.py

from datetime import datetime, timezone

from calmoji.calendar_config import get_year_start_date
from calmoji.calendar_phases import get_semester_phases
from calmoji.types import Phase

UTC = timezone.utc


def _academic_anchor_year_for_today(today: datetime) -> int:
    """
    Academic year anchor:
      - If it's before September, the upcoming academic year starts this calendar year.
      - If it's September or later, the upcoming academic year starts next calendar year.
    """
    return today.year if today.month < 9 else today.year + 1


def test_get_year_start_date_returns_expected_default():
    """Ensure academic alignment returns Sept 1 in the expected anchor year."""
    today = datetime.now(UTC)
    year = _academic_anchor_year_for_today(today)

    start_date = get_year_start_date(year, "academic")

    assert start_date.year == year
    assert start_date.month == 9
    assert start_date.day == 1
    assert start_date.tzinfo is UTC


def test_generated_semester_phases_have_valid_structure():
    """Ensure generated semester phases have valid structure and offsets."""
    today = datetime.now(UTC)
    year = _academic_anchor_year_for_today(today)

    phases = get_semester_phases(year, "academic")

    assert phases, "Expected at least one phase"
    for phase in phases:
        assert isinstance(phase, Phase)
        assert isinstance(phase.name, str)
        assert isinstance(phase.start_offset, int)
        assert isinstance(phase.end_offset, int)
        assert isinstance(phase.emoji, str)

        # Exclusive-end model: end_offset must be strictly greater than start_offset
        assert phase.start_offset < phase.end_offset

        # Enriched phases should have concrete UTC start/end
        assert phase.start is not None
        assert phase.end is not None
        assert phase.start.tzinfo is UTC
        assert phase.end.tzinfo is UTC
        assert phase.start < phase.end  # exclusive end
