"""
🧿 calmoji — Ritual Calendar Generator (UTC, deterministic, glyph-aligned).

A symbolic scheduling engine built on UTC discipline, exclusive time semantics,
and deterministic emoji clocks. See README.md for the full design philosophy.
"""

from __future__ import annotations

import re
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import Optional

# The pyproject.toml of a source checkout sits next to the package folder.
_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"

# Simple line matches, not a TOML parser (there is none in the 3.9 standard library).
_NAME_LINE = re.compile(r'^name\s*=\s*"calmoji"\s*(?:#.*)?$')
_VERSION_LINE = re.compile(r'^version\s*=\s*"([^"]+)"\s*(?:#.*)?$')


def _metadata_version() -> Optional[str]:
    """The installed package's version, or None if calmoji isn't installed."""
    try:
        return _pkg_version("calmoji")
    except PackageNotFoundError:
        return None


def _pyproject_version(path: Path) -> Optional[str]:
    """
    The version = "..." line of calmoji's own pyproject.toml, or None if the file is
    missing, unreadable, isn't calmoji's (no name = "calmoji"), or has no such line.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    if not any(_NAME_LINE.match(line.strip()) for line in lines):
        return None
    for line in lines:
        match = _VERSION_LINE.match(line.strip())
        if match:
            return match.group(1)
    return None


def _resolve_version() -> str:
    """Installed metadata first; from a source checkout, pyproject.toml; else 0.0.0+local."""
    return _metadata_version() or _pyproject_version(_PYPROJECT) or "0.0.0+local"


__version__: str = _resolve_version()

__all__ = ["__version__"]
