# tests/test_calendar_phases.py

import datetime

import pytest

from calmoji.calendar_config import ALIGNMENT_MODES, get_semester_phase_definitions, get_year_start_date
from calmoji.calendar_phases import get_semester_phases
from calmoji.types import Phase


def test_semester_phase_count_matches_definitions():
    year = 2024
    phases = get_semester_phases(year)
    ref_defs = get_semester_phase_definitions()
    assert len(phases) == len(ref_defs)


def test_get_semester_phases_returns_expected_structure():
    year = 2024
    anchor_date = get_year_start_date(year)
    phases = get_semester_phases(year)
    ref_defs = get_semester_phase_definitions()

    assert isinstance(phases, list)
    assert all(isinstance(p, Phase) for p in phases)
    assert len(phases) == len(ref_defs)

    for i, phase in enumerate(phases):
        ref = ref_defs[i]
        expected_start = anchor_date + datetime.timedelta(days=ref.start_offset)
        expected_end = anchor_date + datetime.timedelta(days=ref.end_offset)  # exclusive

        assert phase.name == ref.name
        assert phase.emoji == ref.emoji
        assert phase.start == expected_start
        assert phase.end == expected_end


def test_phase_enrichment_fields_exist():
    phases = get_semester_phases(2024)
    for p in phases:
        assert hasattr(p, "meeting_density")
        assert hasattr(p, "allow_meetings")
        assert hasattr(p, "note")
        assert p.start < p.end  # end is exclusive; must be strictly after start


def test_phase_density_classification():
    phases = get_semester_phases(2024)

    for p in phases:
        if any(kw in p.name for kw in ["Break", "Rest", "Drift"]):
            assert p.meeting_density == "none"
            assert p.allow_meetings is False
        elif any(kw in p.name for kw in ["Downtime", "Prep"]):
            assert p.meeting_density == "low"
            assert p.allow_meetings is True
        elif "Deep Work" in p.name:
            assert p.meeting_density == "high"
            assert p.allow_meetings is True
        else:
            assert p.meeting_density == "normal"
            assert p.allow_meetings is True


def test_phase_duration_computation_is_correct():
    phases = get_semester_phases(2024)

    for p in phases:
        # end is exclusive
        expected = (p.end - p.start).days
        assert p.duration_days == expected, f"{p.name} has incorrect duration: {p.duration_days} ≠ {expected}"


# -----------------------------------------------------------------------------
# Consecutive years fit together exactly (no leap-year gap)
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("alignment", sorted(ALIGNMENT_MODES))
def test_year_n_ends_exactly_where_year_n_plus_1_starts(alignment):
    for year in range(2024, 2041):
        this_year = get_semester_phases(year, alignment)
        next_year = get_semester_phases(year + 1, alignment)

        assert this_year[-1].end == next_year[0].start, f"gap or overlap between {year} and {year + 1} ({alignment})"
        assert this_year[-1].end == get_year_start_date(year + 1, alignment)


@pytest.mark.parametrize("alignment", sorted(ALIGNMENT_MODES))
def test_phases_within_a_year_are_contiguous(alignment):
    for year in (2027, 2028, 2029):
        phases = get_semester_phases(year, alignment)
        assert phases[0].start == get_year_start_date(year, alignment)
        for before, after in zip(phases, phases[1:]):
            assert before.end == after.start


def test_the_leap_day_belongs_to_the_last_phase():
    # 2027 academic runs 2027-09-01 .. 2028-09-01 and so contains 29 Feb 2028.
    last = get_semester_phases(2027, "academic")[-1]
    assert last.end == datetime.datetime(2028, 9, 1, tzinfo=datetime.timezone.utc)
    assert last.start <= datetime.datetime(2028, 8, 31, tzinfo=datetime.timezone.utc) < last.end
    assert last.duration_days == 25
    assert last.end_offset == 366

    # 2028 calendar is itself a leap year: its last phase ends on 2029-01-01.
    last = get_semester_phases(2028, "calendar")[-1]
    assert last.end == datetime.datetime(2029, 1, 1, tzinfo=datetime.timezone.utc)
    assert last.duration_days == 25


def test_ordinary_years_are_unchanged():
    last = get_semester_phases(2029, "calendar")[-1]
    assert last.duration_days == 24
    assert last.end_offset == 365
