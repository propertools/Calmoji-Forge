# Changelog

All notable changes to **calmoji** are recorded in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project (loosely) adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Pre-1.0 releases may break minor compatibility; we will say so loudly when
they do.

## [Unreleased]

### Added

- TBD.

## [0.1.0] — 2026-05-07

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

[Unreleased]: https://github.com/propertools/Calmoji-Forge/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/propertools/Calmoji-Forge/releases/tag/v0.1.0
