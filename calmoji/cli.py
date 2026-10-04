"""
calmoji.cli
-----------
Command-line entry point for the calmoji ritual calendar generator.

Exposed as the ``calmoji`` console script via ``[project.scripts]`` in
``pyproject.toml``, and as ``python -m calmoji`` via ``calmoji/__main__.py``.

The legacy ``calmoji.py`` script at the repository root delegates here so that
existing ``python3 calmoji.py`` invocations continue to work unchanged.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from calmoji import __version__
from calmoji.calendar_config import ALIGNMENT_MODES, DEFAULT_ALIGNMENT
from calmoji.calendar_phases import get_semester_phases
from calmoji.constants import CALNAME_FOCUS, CALNAME_MEETINGS
from calmoji.dry_run import dry_run_months
from calmoji.focus_blocks import generate_focus_blocks_for_phases
from calmoji.ics_writer import write_ebi48_layer, write_semester_blocks
from calmoji.monthly import month_rows, write_monthly_files
from calmoji.output_dir import OutputDirError, check_output_dir, default_output_dir, prepare_output_dir
from calmoji.slot_generator import generate_meeting_slots
from calmoji.types import Event


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="calmoji",
        description="🧿 calmoji — Ritual Calendar Crafter (UTC-fixed)",
    )

    p.add_argument("--year", type=int, required=True, help="Anchor year (e.g., 2027)")
    p.add_argument(
        "--calendar-alignment",
        choices=sorted(ALIGNMENT_MODES),
        default=DEFAULT_ALIGNMENT,
        help="Year alignment mode",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Output directory (default: output/<year>/<alignment>/). "
            "calmoji only writes into a folder that is empty or that it made itself (it holds a "
            ".calmoji-output file), and replaces its own files there on every run"
        ),
    )

    p.add_argument("--dry-run", action="store_true", help="Preview (no file writes)")

    p.add_argument("--no-meetings", action="store_true", help="Do not generate meeting slots")
    p.add_argument("--no-focus", action="store_true", help="Do not generate focus blocks")
    p.add_argument("--no-ebi48", action="store_true", help="Do not emit EBI48 overlay")

    # Meeting slot cadence knobs (stabilized API)
    p.add_argument("--include-oceania", action="store_true", help="Include Auckland/Oceania slots")

    p.add_argument("--version", action="version", version=f"calmoji {__version__}")

    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    outdir: Path = (
        args.output_dir if args.output_dir is not None else default_output_dir(args.year, args.calendar_alignment)
    )

    # Refuse before doing anything else. (--dry-run only reports it: it never touches the filesystem.)
    problem = check_output_dir(outdir)
    if problem is not None and not args.dry_run:
        raise SystemExit(f"error: {problem}")

    print("🦊 calmoji — Initiating Ritual Sequence")
    print("=" * 50)
    print(f"Version: {__version__}")
    print(f"Year: {args.year}")
    print(f"Alignment: {args.calendar_alignment}")
    print(f"Output: {outdir}/")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'WRITE'}")
    if problem is not None:
        print(f"⚠️  A real run would refuse: {problem}")

    # Build phase plan (UTC-aware datetimes inside each Phase)
    phases = get_semester_phases(args.year, args.calendar_alignment)
    for ph in phases:
        if ph.start is None or ph.end is None:
            raise ValueError(f"Phase {ph.name} is missing concrete start/end datetimes.")

    # Focus blocks (clipped to the phases) and meeting slots, for the whole year.
    focus_events: list[Event] = []
    if not args.no_focus:
        focus_events = generate_focus_blocks_for_phases(phases)

    meeting_events: list[Event] = []
    if not args.no_meetings:
        for phase in phases:
            meeting_events.extend(generate_meeting_slots(phase, include_oceania=bool(args.include_oceania)))
        meeting_events.sort(key=lambda e: e.start)

    if args.dry_run:
        print("\n📅 Phases:")
        for ph in phases:
            assert ph.start is not None and ph.end is not None
            print(
                f"  {ph.emoji} {ph.name}: {ph.start.date()} → {ph.end.date()} "
                f"| meetings={ph.allow_meetings} ({ph.meeting_density})"
            )
        if focus_events or meeting_events:
            dry_run_months(
                month_rows(focus_events, meeting_events), focus=not args.no_focus, meetings=not args.no_meetings
            )
    else:
        try:
            prepare_output_dir(outdir)
        except OutputDirError as exc:
            raise SystemExit(f"error: {exc}") from exc

        # 1) Seasons (one all-day marker per phase)
        phases_path = outdir / f"seasons_{args.year}.ics"
        write_semester_blocks(phases, filename=str(phases_path))
        print(f"✅ Wrote: {phases_path}")

        # 2) Focus blocks, one file per month
        for path in write_monthly_files(focus_events, outdir / "focus", "focus", CALNAME_FOCUS):
            print(f"✅ Wrote: {path}")

        # 3) Meeting slots, one file per month
        for path in write_monthly_files(meeting_events, outdir / "meetings", "meetings", CALNAME_MEETINGS):
            print(f"✅ Wrote: {path}")

    # 4) Emoji Clock (EBI48)
    if not args.no_ebi48:
        ebi48_path = outdir / f"emoji_clock_{args.year}.ics"
        if args.dry_run:
            print("\n🧿 Emoji Clock: (skipping file writes in dry-run)")
        else:
            write_ebi48_layer(ebi48_path, args.year, args.calendar_alignment)
            print(f"✅ Wrote: {ebi48_path}")

    print("\n🎉 Ritual complete. Time is now encoded.\n")


if __name__ == "__main__":
    main()
