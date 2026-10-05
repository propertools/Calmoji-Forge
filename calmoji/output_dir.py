# calmoji/output_dir.py

"""
📁 Output folders that never mix runs, and calmoji deletes only what it can prove is its own.

The marker file (.calmoji-output) proves calmoji created a folder. It does not prove calmoji
wrote every file in it now, so ownership is exact. The only paths calmoji may delete are these,
each of them a REGULAR FILE (never a symlink), recognised by name alone (see calmoji/filenames.py):

    seasons_<YYYY>.ics            emoji_clock_<YYYY>.ics            .calmoji-output   (top level)
    focus/focus_<YYYY>-<MM>.ics   meetings/meetings_<YYYY>-<MM>.ics

Any year is fine, so re-running for 2028 cleans up 2027's files. Everything else is foreign:
another .ics file (family.ics, focus/my-calendar.ics), any symlink at any level (including
focus/ and meetings/ themselves), any subfolder inside focus/ or meetings/, anything at all.

    missing or empty        create it and write
    genuine marker          delete the owned files one at a time, then rmdir focus/ and
                            meetings/ once empty (no recursive delete), then write fresh;
                            if anything foreign is present, refuse and delete NOTHING
    anything else           refuse, touching nothing

A marker is genuine only if it is a regular file (not a symlink) whose content is exactly
OUTPUT_MARKER_TEXT. It is also written without following a link where the platform allows
(O_NOFOLLOW), so a symlink swapped in can't redirect the write.

macOS's .DS_Store (Finder writes one into any folder you open): at the top level it is looked
past: neither refused nor deleted, and it doesn't make a folder "non-empty". Inside focus/ and
meetings/ it may be deleted, so those folders can be removed (Finder recreates it).
"""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import List, Optional

from calmoji.constants import OUTPUT_MARKER_NAME, OUTPUT_MARKER_TEXT
from calmoji.filenames import SUBFOLDER_FILES, is_subfolder_calmoji_file, is_top_level_calmoji_file

OWNED_DIRECTORIES = tuple(SUBFOLDER_FILES)  # ("focus", "meetings")
IGNORED_NAMES = frozenset({".DS_Store"})


class OutputDirError(ValueError):
    """The output folder can't be used safely. Nothing was written or deleted."""


def default_output_dir(year: int, alignment: str) -> Path:
    """The folder used when --output-dir isn't given: output/<year>/<alignment>/."""
    return Path("output") / str(year) / alignment


# ── Looking at paths without following links ─────────────────────────────────


def _mode(path: Path) -> Optional[int]:
    try:
        return path.lstat().st_mode
    except OSError:
        return None


def _is_regular_file(path: Path) -> bool:
    """A regular file itself: not a symlink to one, not a directory."""
    mode = _mode(path)
    return mode is not None and stat.S_ISREG(mode)


def _is_real_directory(path: Path) -> bool:
    """A directory itself: not a symlink to one."""
    mode = _mode(path)
    return mode is not None and stat.S_ISDIR(mode)


def _describe(path: Path, label: str) -> str:
    """How a foreign path is named in a message."""
    mode = _mode(path)
    if mode is not None and stat.S_ISLNK(mode):
        return f"{label} (a symlink)"
    if mode is not None and stat.S_ISDIR(mode):
        return f"{label}/"
    return label


def _contents(path: Path) -> List[Path]:
    return sorted(p for p in path.iterdir() if p.name not in IGNORED_NAMES)


# ── The marker ───────────────────────────────────────────────────────────────


def _marker_is_genuine(outdir: Path) -> bool:
    marker = outdir / OUTPUT_MARKER_NAME
    if not _is_regular_file(marker):
        return False
    if marker.lstat().st_size != len(OUTPUT_MARKER_TEXT.encode("utf-8")):
        return False
    return marker.read_bytes() == OUTPUT_MARKER_TEXT.encode("utf-8")


def _write_marker(outdir: Path) -> None:
    """
    Write the marker without following a symlink: O_NOFOLLOW where the platform has it,
    and (always) a check beforehand, so a symlink there is refused rather than written through.
    """
    marker = outdir / OUTPUT_MARKER_NAME
    mode = _mode(marker)
    if mode is not None and not stat.S_ISREG(mode):
        raise OutputDirError(f"{marker} isn't a regular file, so calmoji won't write through it.")

    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(marker, flags, 0o644)
    except OSError as exc:  # ELOOP when a symlink was swapped in after the check above
        raise OutputDirError(f"couldn't write {marker} safely: {exc.strerror}") from exc
    with os.fdopen(fd, "wb") as handle:
        handle.write(OUTPUT_MARKER_TEXT.encode("utf-8"))


# ── What is foreign ──────────────────────────────────────────────────────────


def _foreign_paths(outdir: Path) -> List[str]:
    """Everything in a marked folder that isn't exactly calmoji's own (read-only)."""
    foreign: List[str] = []
    for entry in _contents(outdir):
        if entry.name == OUTPUT_MARKER_NAME:
            continue  # genuine: checked before this is called
        if entry.name in OWNED_DIRECTORIES:
            if not _is_real_directory(entry):
                foreign.append(_describe(entry, entry.name))
                continue
            for child in sorted(entry.iterdir()):
                label = f"{entry.name}/{child.name}"
                if child.name == ".DS_Store" and _is_regular_file(child):
                    continue  # removable, so the folder can go
                if not (_is_regular_file(child) and is_subfolder_calmoji_file(entry.name, child.name)):
                    foreign.append(_describe(child, label))
        elif not (_is_regular_file(entry) and is_top_level_calmoji_file(entry.name)):
            foreign.append(_describe(entry, entry.name))
    return foreign


def check_output_dir(outdir: Path) -> Optional[str]:
    """
    Say why calmoji must refuse to write into outdir, or return None if it may.
    Read-only: touches nothing.
    """
    if not outdir.exists():
        return None
    if not outdir.is_dir():
        return f"{outdir} exists and is not a folder. Choose another --output-dir."

    if not _contents(outdir):
        return None

    marker = outdir / OUTPUT_MARKER_NAME
    if not _marker_is_genuine(outdir):
        why = (
            f"it has a {OUTPUT_MARKER_NAME} that isn't calmoji's own (it isn't a plain file with calmoji's text)"
            if _mode(marker) is not None
            else f"it has no {OUTPUT_MARKER_NAME} file"
        )
        return (
            f"{outdir} isn't empty, and calmoji didn't create it ({why}), "
            "so calmoji won't write into it or delete anything there. "
            "Use an empty folder, or choose another --output-dir."
        )

    foreign = _foreign_paths(outdir)
    if foreign:
        listed = ", ".join(foreign)
        return (
            f"{outdir} is a calmoji folder, but it also holds files calmoji didn't write: {listed}. "
            "calmoji only deletes files it recognises by name, and won't delete anything. "
            "Move them out, or choose another --output-dir."
        )
    return None


# ── Cleaning ─────────────────────────────────────────────────────────────────


def _unlink_owned_file(path: Path, owned: bool) -> None:
    """Unlink one file, but only if it is still a regular file calmoji owns."""
    if not (owned and _is_regular_file(path)):
        raise OutputDirError(f"{path} changed while calmoji was cleaning; stopping without deleting it.")
    path.unlink()


def _clean(outdir: Path) -> None:
    """Delete calmoji's own previous files one at a time, then rmdir its two subfolders."""
    for entry in sorted(outdir.iterdir()):
        if entry.name in IGNORED_NAMES or entry.name == OUTPUT_MARKER_NAME or entry.name in OWNED_DIRECTORIES:
            continue
        _unlink_owned_file(entry, is_top_level_calmoji_file(entry.name))

    for name in OWNED_DIRECTORIES:
        folder = outdir / name
        if _mode(folder) is None:
            continue  # not there
        if not _is_real_directory(folder):
            raise OutputDirError(f"{folder} changed while calmoji was cleaning; stopping.")
        for child in sorted(folder.iterdir()):
            owned = is_subfolder_calmoji_file(name, child.name) or child.name == ".DS_Store"
            _unlink_owned_file(child, owned)
        folder.rmdir()  # fails (and so stops) if anything is left


def prepare_output_dir(outdir: Path) -> None:
    """
    Make outdir ready for a fresh run: create it, or clear calmoji's own previous files from
    it, and make sure the marker is in place.

    Raises OutputDirError, before changing anything, if check_output_dir() refuses.
    """
    problem = check_output_dir(outdir)
    if problem is not None:
        raise OutputDirError(problem)

    outdir.mkdir(parents=True, exist_ok=True)
    _write_marker(outdir)  # first, so a run that stops half-way leaves a folder calmoji recognises
    _clean(outdir)
