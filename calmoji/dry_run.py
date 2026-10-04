# calmoji/dry_run.py

from __future__ import annotations

from typing import Sequence

from calmoji.monthly import MonthRow


def dry_run_months(rows: Sequence[MonthRow], *, focus: bool = True, meetings: bool = True) -> None:
    """
    Print what a real run would write: one row per month (UTC), with the counts of
    focus blocks, Glyph Keys and meeting slots in that month's files.

    A layer that was switched off (--no-focus / --no-meetings) shows '-'.
    """

    def cell(value: int, shown: bool) -> str:
        return str(value) if shown else "-"

    print("\n📆 Monthly files (UTC): focus/focus_<YYYY-MM>.ics and meetings/meetings_<YYYY-MM>.ics")
    print(f"{'Month':<9}{'Focus blocks':>14}{'Glyph Keys':>12}{'Meeting slots':>15}")
    print("─" * 50)
    for row in rows:
        print(
            f"{row.month:<9}{cell(row.focus_blocks, focus):>14}"
            f"{cell(row.glyph_keys, focus):>12}{cell(row.meeting_slots, meetings):>15}"
        )
    print("─" * 50)
    print(
        f"{'Total':<9}{cell(sum(r.focus_blocks for r in rows), focus):>14}"
        f"{cell(sum(r.glyph_keys for r in rows), focus):>12}{cell(sum(r.meeting_slots for r in rows), meetings):>15}"
    )
    print(f"{len(rows)} months\n")
