# Changelog

All notable changes to **calmoji** are recorded in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project (loosely) adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Pre-1.0 releases may break minor compatibility; we will say so loudly when
they do.

## [Unreleased]

## [0.1.2] — 2026-10-04

**The calendar files are unchanged.** v0.1.2 produces byte-for-byte the same
`.ics` files as v0.1.1, so there is nothing to re-import. It hardens the
Python API and the command line, and corrects the docs, after an external
review.

### Fixed

- **Every TEXT value is now escaped** as RFC 5545 §3.3.11 requires: `\`, `;`,
  `,` and line breaks. Before, only newlines in `DESCRIPTION` were, and
  `SUMMARY` wasn't escaped at all, so an event titled
  `"Hello\nATTENDEE:mailto:x@example.com"` injected a second property.
  `SUMMARY`, `DESCRIPTION`, `COMMENT`, `NAME` and `X-WR-CALNAME` all go
  through the new `escape_ics_text()`; `UID` and `RRULE` aren't text, so a
  line break in either is rejected instead. calmoji's own text never
  contained a backslash, semicolon or comma, and its newlines were already
  escaped, which is why the files don't change.
- **Unknown alignments raise.** `get_year_start_date(2027, "acadmeic")` used
  to fall back to `academic` silently. It now raises `ValueError` naming the
  bad value and listing the valid ones.
- **A stricter `Event`.** A timed event whose end isn't after its start
  raises. All-day events follow one documented rule: an end at midnight is
  exclusive; an end with a time of day means "through that date", so it
  becomes the next midnight (08:00 to 23:00 on one date is a one-day all-day
  event, which used to raise); an end date before the start date raises.
- **`--version` works from a source checkout.** `python3 calmoji.py --version`
  in a clone that isn't installed printed `calmoji 0.0.0+local`. It now reads
  the version from the `pyproject.toml` next to the package, and keeps
  `0.0.0+local` only if that file can't be found or read.

### Changed

- **Output folders never mix runs.** `--output-dir` now defaults to
  `output/<year>/<alignment>/` (it was `output/`); an explicit `--output-dir`
  is used as given. calmoji writes a small `.calmoji-output` marker into every
  folder it fills, and only ever cleans a folder that has it. On a re-run it
  replaces its own files (`focus/`, `meetings/`, the top-level `.ics` files)
  and refuses, deleting nothing, if anything else is in the folder. A
  non-empty folder without the marker is refused untouched, with a message
  suggesting an empty folder or another `--output-dir`. Before, generating
  2027 `academic` and then `calendar` into one folder left 20 monthly focus
  files, and re-running with `--no-meetings` left the old `meetings/` behind.
  `--dry-run` never touches the filesystem, and macOS's `.DS_Store` is
  ignored. The release bundle doesn't contain the marker, and the bundle
  README's "regenerate and compare" recipe now excludes it.

### Removed

- **The placeholder alignments `chinese_lunar` and `islamic_hijri`.** They
  were a fixed 10 February and a fixed 7 July, not real calendars, but the
  command line offered them as if they were. They may return later,
  implemented properly.

### Documentation

- The README no longer says `scripts/preflight.sh` runs every check CI runs:
  preflight runs CI's main checks on your machine, and CI also tests Python
  3.9 through 3.13, compares output across Python versions, and runs on stock
  macOS. It documents the new output folder, names the download by pattern
  (`calmoji-artifacts-vX.Y.Z.zip`) so it needs no edit each release, and
  explains that `DTSTAMP` is a fixed, documented constant so files stay
  reproducible.
- `CONTRIBUTING.md`'s roadmap no longer lists finished work, and its
  "coverage of at least 90%" is now enforced (`fail_under = 90`; total branch
  coverage is 94%). `TEST_STRATEGY.md` drops Codecov, calls the per-module
  numbers targets rather than gates, and lists only the gates CI really has.
- `scripts/preflight.sh` suggests the release steps, not `gh pr create`, when
  it runs on `main`.
- The playbook ends with an optional section on using an AI assistant as an
  agenda steward, with a starting prompt, and the README points to it. calmoji
  itself still needs no AI, account or cloud service.
- Screenshots in the README and the playbook: a made-up week with The Map on
  and off, claiming a block, the calendar list and its colours, the Emoji
  Clock beside the meeting slots, and a slot's description.
- The README says plainly what calmoji means for your data: it never sees
  your calendar, and because almost every calendar app imports and exports
  `.ics`, there's no lock-in. Its download section now opens with four quick
  steps.

## [0.1.1] — 2026-10-04

**Upgrading from v0.1.0: delete the old calmoji calendars and import fresh.**
Event times and identifiers changed, so importing over the old events would
leave you with duplicates.

### Changed

- **Focus blocks and meeting slots are now one file per month**, in
  `focus/` and `meetings/` (for example `2027/academic/focus/focus_2027-09.ics`).
  Calendar apps cap imports (reported: Proton 15,000 events and 10 MB, Google
  about 1 MB per file, Outlook failing somewhere around 700 events), and
  v0.1.0's biggest files could exceed them. Each event is in exactly one file,
  the month of its start in UTC, and only months that have events get a file.
  The weekly `focus_weeks/` folder, `meeting_all_<year>.ics` and the per-phase
  meeting files are gone. `calmoji --dry-run` prints a month-by-month summary.
- **Every `.ics` file stays under 600 events and 512 KB**, and calmoji refuses
  to write one that wouldn't. The largest file for any alignment and any year
  2026–2039 is 377 events and 131,352 bytes.
- **The ready-made calendars now cover 2026–2036** instead of 2026–2039,
  because Proton accepts events only up to the end of 2037 and the 2037
  `academic` year runs into 2038. Any year can still be generated by hand.
- **`--year` is required.** Its default of 2025 was stale.
- **The layers are renamed, and the calendar name inside each file now
  matches the recommended calendar**: 🌗 Seasons (was Semester Phases),
  🧠 Focus — Open, 🕒 Meetings — Open and 🧿 Emoji Clock (was the EBI48
  clock). The same name is used in every file of a layer, so apps that
  create a calendar on import name it correctly and repeated imports look
  consistent. The files are renamed to match: `semester_phases_<year>.ics`
  is now `seasons_<year>.ics` and `ebi48_layer_<year>.ics` is now
  `emoji_clock_<year>.ics`. The names no longer say "(UTC)": every time is
  UTC and your app shows it in local time. The playbook groups the
  calendars as The Map (calmoji's layers), Commitments, Life and Sandbox,
  and suggests a calm colour palette.
- `scripts/preflight.sh` reads the expected version from `pyproject.toml`
  instead of hardcoding it, and its bundle gate (9) now builds a two-year
  release bundle twice and checks that the archives are byte-identical and the
  manifest verifies, instead of checking a local, gitignored folder.
  It also no longer insists on seven commits ahead of `main`, a rule left
  over from the one-off OSS-release branch.
- README rewritten for people using the calendars, with known limitations and a v0.2 roadmap.
- New `docs/PLAYBOOK.md` describing the layered calendar pattern (replaces `CALENDAR_SYSTEM.md`).
- The v0.1.0 release also offers a `.zip`, and the bundle's own README no longer points at ebi48.org.

### Added

- `scripts/build_bundle.py` builds the release archives
  (`calmoji-artifacts-v<version>.zip` and `.tar.gz`) in both alignments,
  with a `MANIFEST.sha256` and a README. It fails if any file is over the size
  budget, and prints the file count, the largest file, the archive sizes and
  their checksums. Running it twice on the same machine gives byte-identical
  archives.
- A "Releasing" section in `CONTRIBUTING.md`.

### Fixed

- **Meeting slot titles no longer carry a local time**, because the
  hand-written times were often false: in winter, Brussels, Havana and Seattle
  slots fall an hour earlier than their labels said. Slots stay fixed in UTC
  all year, like everything in calmoji, and your calendar app shows them in
  your local time. Each slot's description now says when it falls locally, in
  summer and in winter (for example "13:35–14:00 CEST in summer and
  12:35–13:00 CET in winter. Fixed at 11:35 UTC."). Two cities moved to their
  intended early-afternoon times: Delhi to 08:05 and 08:35 UTC (13:35 and
  14:05 IST; the slots were labelled 12:35 and 13:05 but really fell at
  13:05 and 13:35), and Auckland, with `--include-oceania`, to 02:35 and 03:05 UTC
  (15:35 and 16:05 NZDT; they fell in the evening). Every other city keeps
  its UTC times.
- **The 🧿 Emoji Clock (EBI48) now appears every day.** v0.1.0 repeated each of its 48
  events weekly with `COUNT=52`, so the clock showed one day a week, and
  Proton rejected the import because it caps repeats at 50. Each event now
  repeats daily until the start of the next year, with no `COUNT`. A summary
  shows its emoji once instead of twice, there is a single all-day
  "🗝️ EBI48 Glyph Key", and descriptions link to the EBI48 README on GitHub
  instead of ebi48.org, which isn't live yet.
- **Every event now has a `DTSTAMP`**, which RFC 5545 requires and strict
  calendar apps may insist on. It is a fixed value, so output stays
  byte-for-byte reproducible.
- **Focus blocks no longer appear twice where one phase meets the next.**
  v0.1.0 emitted whole ISO weeks for each phase, so a week that straddled two
  phases was written twice (336 to 588 duplicated focus-block start times a
  year). Each block now appears once, in the phase and month it starts.
- **The leap-year gap is closed.** The last phase now ends at the next year's
  start, so in a leap year the final day (31 August 2028 in `academic`,
  31 December 2028 in `calendar`) no longer belongs to no year, and
  consecutive years fit together exactly.

### Removed

For anyone using the Python API: `write_focus_blocks_weekly()` and
`focus_blocks_writer.py`, the `recurring` and `expanded` options of
`write_ebi48_layer()` (which now takes the alignment), `dry_run()` (replaced
by `dry_run_months()`), and the hand-written label column in `MEETING_SLOTS`.

## [0.1.0] — 2026-10-04

First public release. The engine has been in private use for some time;
this release is the cleanup pass that makes it safe to read, install, and
audit.

### Added

- Installable Python package with PEP 621 metadata in `pyproject.toml`.
- Console script `calmoji` and module entry point `python -m calmoji`.
- `--version` flag sourced from package metadata via `importlib.metadata`.
- `py.typed` marker for downstream type checkers.
- Runs on Python 3.9 and newer, including the `python3` that ships with
  macOS, with no third-party runtime dependencies.
- Continuous integration: pytest with branch coverage on Python 3.9
  through 3.13, ruff/black/mypy against the 3.9 floor, and a no-install
  run on the stock macOS `python3`.
- A determinism check in CI that runs the generator twice with identical
  inputs, and on both Python 3.9 and 3.13, and diffs the outputs
  byte-for-byte.
- `SECURITY.md` describing the coordinated-disclosure policy.
- `CHANGELOG.md` (this file).
- Pre-generated `.ics` artifact bundle covering 2026–2039 in both
  `academic` and `calendar` alignments, distributed as a GitHub Release
  asset and mirrored at [ebi48.org](https://ebi48.org). The bundle ships
  with a `MANIFEST.sha256` so consumers can verify provenance.

### Changed

- Reorganized: the CLI implementation moved from the root `calmoji.py`
  into `calmoji/cli.py`. The root `calmoji.py` is now a thin shim so that
  `python3 calmoji.py --year=...` continues to work for users who clone
  the repo without installing.
- README reframed around the artifact-import path (most users) ahead of
  the generator install path (developers and regenerators).

### Fixed

- `Makefile` `type` target referenced `mypy forge`; corrected to
  `mypy calmoji`.
- README post-clone instruction said `cd calmoji`; corrected to
  `cd Calmoji-Forge`.
- `EBI48-README.md` had two malformed code fences and a stray closing
  fence; cleaned up so the document renders correctly on GitHub.
- Static `51 passed / 0 failed` test claim removed from the README; the
  CI badge will carry that information once it is wired up.

### Security

- No known security issues at the time of this release. Reporting channel
  documented in `SECURITY.md`.

[Unreleased]: https://github.com/propertools/Calmoji-Forge/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/propertools/Calmoji-Forge/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/propertools/Calmoji-Forge/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/propertools/Calmoji-Forge/releases/tag/v0.1.0
