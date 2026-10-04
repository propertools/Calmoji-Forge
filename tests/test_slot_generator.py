# tests/test_slot_generator.py

from calmoji.calendar_phases import get_semester_phases
from calmoji.slot_generator import generate_meeting_slots
from calmoji.types import Event


def test_slot_generation_for_first_phase():
    phases = get_semester_phases(2025, "academic")
    phase = phases[0]
    events = generate_meeting_slots(phase)

    assert len(events) > 0

    for evt in events:
        assert isinstance(evt, Event)
        assert evt.start is not None
        assert evt.end is not None
        assert isinstance(evt.summary, str)
        assert isinstance(evt.description, str)

        assert "Face" in evt.summary  # Emoji time label

        if "Mecca" in evt.summary:
            assert evt.start.weekday() in {6, 0, 1, 2, 3}  # Sunday–Thursday
        else:
            assert evt.start.weekday() in {0, 1, 2, 3, 4}  # Monday–Friday


def test_all_events_within_phase_range():
    phases = get_semester_phases(2025, "academic")
    phase = phases[0]
    events = generate_meeting_slots(phase)

    # Exclusive end semantics:
    # - event start must be strictly < phase.end
    # - event end must be <= phase.end (end can touch boundary only if it lands exactly at phase.end)
    for evt in events:
        assert phase.start <= evt.start < phase.end
        assert evt.end <= phase.end
        assert evt.start.date() == evt.end.date()
