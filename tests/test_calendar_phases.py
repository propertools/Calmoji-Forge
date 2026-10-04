# tests/test_calendar_phases.py

import datetime

from calmoji.calendar_config import get_semester_phase_definitions, get_year_start_date
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
