# tests/test_ics_output.py

import datetime
from calmoji.calendar_phases import get_semester_phases
from calmoji.slot_generator import generate_meeting_slots
from calmoji.ics_writer import create_ics_header, create_ics_footer
from calmoji.calendar_config import get_year_start_date
from calmoji.types import Event
from calmoji.generator import get_all_events



def make_test_event() -> Event:
    """Return a minimal test Event."""
    start = datetime.datetime(2024, 9, 15, 13, 35)
    return Event(
        start=start,
        end=start + datetime.timedelta(minutes=25),
        summary="Test Slot",
        description="Test Description",
        emoji="🦊",
    )


def test_ics_file_line_count(tmp_path):
    testfile = tmp_path / "test_output.ics"

    # Compose .ics content
    event = make_test_event()
    ics_content = (
        "\n".join(create_ics_header()) + "\n" +
        "\n".join(event.to_ics()) + "\n" +
        "\n".join(create_ics_footer()) + "\n"
    )
    testfile.write_text(ics_content, encoding="utf-8")

    # Read and inspect
    lines = testfile.read_text(encoding="utf-8").splitlines()

    # Assertions
    assert any("UID:" in line for line in lines), "Missing UID"
    assert any("BEGIN:VEVENT" in line for line in lines), "Missing BEGIN:VEVENT"
    assert any("END:VEVENT" in line for line in lines), "Missing END:VEVENT"
    assert len(lines) > 10, f"Expected .ics to be longer than 10 lines, got {len(lines)}"
