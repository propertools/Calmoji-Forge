# tests/test_utils_high_impact.py

import unittest
from datetime import datetime, timezone

from calmoji.utils import format_datetime, group_phase_days_by_week
from calmoji.ics_writer import create_ics_header, fold_ics_line
from calmoji.types import Phase, PhaseWeekSpan

UTC = timezone.utc


class TestCalmojiUtilsHighImpact(unittest.TestCase):
    def test_ics_header_contains_required_fields(self):
        """Ensure ICS header includes expected fields and comments."""
        header = create_ics_header(
            calname="test calendar",
            comments=["test comment"],
        )

        self.assertEqual(header[0], "BEGIN:VCALENDAR")
        self.assertTrue(any("PRODID:" in line for line in header))
        self.assertIn("NAME:test calendar", header)
        self.assertIn("X-WR-CALNAME:test calendar", header)
        self.assertIn("COMMENT:test comment", header)

    def test_group_phase_days_by_week_handles_year_boundary(self):
        """
        Dec 30, 2024 to Jan 6, 2025 spans ISO week 2025-W01.
        Phase.end is exclusive, so Jan 6 is the exclusive boundary.
        Ensure it produces exactly one PhaseWeekSpan with Monday 2024-12-30.
        """
        phase = Phase(
            name="Cross-Year",
            start=datetime(2024, 12, 30, 0, 0, tzinfo=UTC),
            end=datetime(2025, 1, 6, 0, 0, tzinfo=UTC),  # exclusive end
            start_offset=0,
            end_offset=7,
            emoji="📆",
        )

        grouped = group_phase_days_by_week(phase)

        self.assertEqual(len(grouped), 1)
        self.assertIsInstance(grouped[0], PhaseWeekSpan)
        self.assertEqual(grouped[0].iso_week_label, "2025-W01")
        self.assertEqual(grouped[0].start, datetime(2024, 12, 30, 0, 0, tzinfo=UTC))

    def test_folded_ics_lines_are_wrapped_or_long(self):
        """ICS lines must fold after 75 octets per RFC 5545."""
        dt = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
        long_line = f"DTSTART:{format_datetime(dt)}" + "A" * 200
        folded = fold_ics_line(long_line)

        # fold_ics_line uses CRLF; accept either CRLF or LF depending on splitlines behavior
        self.assertTrue("\r\n" in folded or "\n" in folded)
        self.assertTrue(any(line.startswith(" ") for line in folded.splitlines()[1:]))


if __name__ == "__main__":
    unittest.main()