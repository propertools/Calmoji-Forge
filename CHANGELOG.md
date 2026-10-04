# Changelog

All notable changes to **calmoji** are recorded in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project (loosely) adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Pre-1.0 releases may break minor compatibility; we will say so loudly when
they do.

## [Unreleased]

## [0.1.1] — YYYY-MM-DD

A small release: focus blocks now work like meeting slots, and the release
archives are built by a script.

### Changed

- **Focus-block output has changed.** Focus blocks are now written per phase,
  clipped to the phase's dates, instead of one file per ISO week:
  - one file per phase, `focus_<phase>_<from>_to_<to>.ics`, holding exactly
    the blocks that start inside that phase (`[start, end)`, end exclusive),
    with the weekly 🗝️ Glyph Key on each Monday that falls inside it;
  - one consolidated file per year, `focus_all_<year>.ics`, holding exactly
    the union of the per-phase files;
  - the weekly files and the `focus_weeks/` folder are gone.

  A phase no longer includes days from before its start or after its end,
  so a week that straddles two phases is no longer emitted twice. Events
  keep the same summaries, descriptions and UIDs as in v0.1.0. If you
  imported v0.1.0's weekly focus files, delete that focus calendar and
  import the new files. Each year's output drops from 65–68 `.ics` files to
  17.
- `calmoji --dry-run` now previews focus blocks per phase, the way it
  previews meeting slots.
- `scripts/preflight.sh` reads the expected version from `pyproject.toml`
  instead of hardcoding it, and its bundle gate (9) now builds the release
  bundle twice and checks that the archives are byte-identical and the
  manifest verifies, instead of checking a local, gitignored folder.
  It also no longer insists on seven commits ahead of `main`, a rule left
  over from the one-off OSS-release branch.
- README rewritten for people using the calendars, with known limitations and a v0.2 roadmap.
- New `docs/PLAYBOOK.md` describing the layered calendar pattern (replaces `CALENDAR_SYSTEM.md`).
- The v0.1.0 release also offers a `.zip`, and the bundle's own README no longer points at ebi48.org.

### Added

- `scripts/build_bundle.py` builds the release archives
  (`calmoji-artifacts-v<version>.zip` and `.tar.gz`) for 2026–2039 in both
  alignments, with a `MANIFEST.sha256` and a README, and prints their
  checksums. Running it twice gives byte-identical archives.
- A "Releasing" section in `CONTRIBUTING.md`.

### Removed

- `calmoji.focus_blocks_writer.write_focus_blocks_weekly()`, replaced by
  `write_focus_blocks()`, which writes the per-phase and per-year files.

### Fixed

- Focus blocks at phase boundaries were emitted twice: 336–588 duplicated
  focus-block start times per year in v0.1.0, measured across 2026–2039 in
  both alignments. There are none now.

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

[Unreleased]: https://github.com/propertools/Calmoji-Forge/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/propertools/Calmoji-Forge/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/propertools/Calmoji-Forge/releases/tag/v0.1.0
