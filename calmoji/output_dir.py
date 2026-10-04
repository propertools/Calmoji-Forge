# calmoji/output_dir.py

"""
📁 Output folders that never mix runs.

A successful run leaves exactly what it describes. To make that safe, calmoji only
ever cleans a folder it can prove it made: one that holds the ownership marker
(.calmoji-output). Anything else that isn't empty is refused, untouched.

    missing or empty       create it and write
    has the marker         remove calmoji's own paths, then write fresh;
                           refuse (deleting nothing) if anything else is in there
    non-empty, no marker   refuse

calmoji's own paths are focus/, meetings/, the top-level *.ics files and the marker.
The one thing it looks past is macOS's .DS_Store (Finder writes one into any folder
you open): it is neither refused nor deleted, and doesn't make a folder "non-empty".
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Optional

from calmoji.constants import OUTPUT_MARKER_NAME, OUTPUT_MARKER_TEXT

OWNED_DIRECTORIES = ("focus", "meetings")
IGNORED_NAMES = frozenset({".DS_Store"})


class OutputDirError(ValueError):
    """The output folder can't be used safely. Nothing was written or deleted."""


def default_output_dir(year: int, alignment: str) -> Path:
    """The folder used when --output-dir isn't given: output/<year>/<alignment>/."""
    return Path("output") / str(year) / alignment


def _contents(path: Path) -> List[Path]:
    return sorted(p for p in path.iterdir() if p.name not in IGNORED_NAMES)


def _unexpected_paths(outdir: Path) -> List[str]:
    """Everything in a marked folder that isn't calmoji's (read-only)."""
    unexpected: List[str] = []
    for entry in _contents(outdir):
        if entry.name == OUTPUT_MARKER_NAME:
            continue
        if entry.name in OWNED_DIRECTORIES:
            if entry.is_symlink() or not entry.is_dir():
                unexpected.append(entry.name)
                continue
            for child in _contents(entry):
                if not (child.is_file() and child.name.endswith(".ics")):
                    unexpected.append(f"{entry.name}/{child.name}")
        elif not (entry.is_file() and entry.name.endswith(".ics")):
            unexpected.append(entry.name + ("/" if entry.is_dir() and not entry.is_symlink() else ""))
    return unexpected


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
    if not marker.is_file():
        return (
            f"{outdir} isn't empty, and calmoji didn't create it (it has no {OUTPUT_MARKER_NAME} file), "
            "so calmoji won't write into it or delete anything there. "
            "Use an empty folder, or choose another --output-dir."
        )

    unexpected = _unexpected_paths(outdir)
    if unexpected:
        listed = ", ".join(unexpected)
        return (
            f"{outdir} is a calmoji folder, but it also holds files calmoji didn't write: {listed}. "
            "calmoji won't delete anything. Move them out, or choose another --output-dir."
        )
    return None


def prepare_output_dir(outdir: Path) -> None:
    """
    Make outdir ready for a fresh run: create it, or clear calmoji's own previous files
    from it, then write the marker.

    Raises OutputDirError, before changing anything, if check_output_dir() refuses.
    """
    problem = check_output_dir(outdir)
    if problem is not None:
        raise OutputDirError(problem)

    outdir.mkdir(parents=True, exist_ok=True)
    for name in OWNED_DIRECTORIES:
        owned = outdir / name
        if owned.is_dir() and not owned.is_symlink():
            shutil.rmtree(owned)
    for old in outdir.glob("*.ics"):
        old.unlink()

    (outdir / OUTPUT_MARKER_NAME).write_bytes(OUTPUT_MARKER_TEXT.encode("utf-8"))
