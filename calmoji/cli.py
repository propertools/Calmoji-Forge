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
from calmoji.dry_run import dry_run
from calmoji.focus_blocks import generate_focus_blocks_for_phase
from calmoji.focus_blocks_writer import write_focus_blocks
from calmoji.ics_writer import write_ebi48_layer, write_events_to_ics, write_semester_blocks
from calmoji.slot_generator import generate_meeting_slots
from calmoji.utils import format_range_slug, slugify


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="calmoji",
        description="🧿 calmoji — Ritual Calendar Crafter (UTC-fixed)",
    )

    p.add_argument("--year", type=int, default=2025, help="Anchor year (e.g., 2025)")
    p.add_argument(
        "--calendar-alignment",
        choices=sorted(ALIGNMENT_MODES),
        default=DEFAULT_ALIGNMENT,
        help="Year alignment mode",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Output directory (default: output/)",
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

    outdir: Path = args.output_dir

    print("🦊 calmoji — Initiating Ritual Sequence")
    print("=" * 50)
    print(f"Version: {__version__}")
    print(f"Year: {args.year}")
    print(f"Alignment: {args.calendar_alignment}")
    print(f"Output: {outdir}/")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'WRITE'}")

    # Build phase plan (UTC-aware datetimes inside each Phase)
    phases = get_semester_phases(args.year, args.calendar_alignment)

    if args.dry_run:
        print("\n📅 Phases:")
        for ph in phases:
            if ph.start is None or ph.end is None:
                raise ValueError(f"Phase {ph.name} is missing concrete start/end datetimes.")
            print(
                f"  {ph.emoji} {ph.name}: {ph.start.date()} → {ph.end.date()} "
                f"| meetings={ph.allow_meetings} ({ph.meeting_density})"
            )
    else:
        outdir.mkdir(parents=True, exist_ok=True)

        # 1) Semester phase markers
        phases_path = outdir / f"semester_phases_{args.year}.ics"
        write_semester_blocks(phases, filename=str(phases_path))
        print(f"✅ Wrote: {phases_path}")

    # 2) Meeting slots
    all_meeting_events = []
    if not args.no_meetings:
        for phase in phases:
            if not phase.allow_meetings:
                continue
            if phase.start is None or phase.end is None:
                raise ValueError(f"Phase {phase.name} is missing concrete start/end datetimes.")

            events = generate_meeting_slots(
                phase,
                include_oceania=bool(args.include_oceania),
            )
            all_meeting_events.extend(events)

            target = outdir / f"meeting_{slugify(phase.name)}_{format_range_slug(phase.start, phase.end)}.ics"

            if args.dry_run:
                dry_run(events, label=phase.name, kind="meeting slots")
            else:
                write_events_to_ics(events, target, calname=f"🧿 calmoji — Meetings — {phase.name} (UTC)")
                print(f"✅ Wrote: {target}")

        if not args.dry_run:
            consolidated = outdir / f"meeting_all_{args.year}.ics"
            write_events_to_ics(
                all_meeting_events,
                consolidated,
                calname=f"🧿 calmoji — Meetings (All) {args.year} (UTC)",
            )
            print(f"✅ Wrote: {consolidated}")

    # 3) Focus blocks (one file per phase, plus one consolidated file for the year)
    if not args.no_focus:
        if args.dry_run:
            for phase in phases:
                dry_run(generate_focus_blocks_for_phase(phase), label=phase.name, kind="focus blocks")
        else:
            for path in write_focus_blocks(phases, outdir, args.year):
                print(f"✅ Wrote: {path}")

    # 4) EBI48 overlay
    if not args.no_ebi48:
        ebi48_path = outdir / f"ebi48_layer_{args.year}.ics"
        if args.dry_run:
            print("\n🧿 EBI48 overlay: (skipping file writes in dry-run)")
        else:
            write_ebi48_layer(ebi48_path, args.year, recurring=True, expanded=False)
            print(f"✅ Wrote: {ebi48_path}")

    print("\n🎉 Ritual complete. Time is now encoded.\n")


if __name__ == "__main__":
    main()
