"""
🧿 calmoji — Ritual Calendar Generator (UTC, deterministic, glyph-aligned).

A symbolic scheduling engine built on UTC discipline, exclusive time semantics,
and deterministic emoji clocks. See README.md for the full design philosophy.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    __version__: str = _pkg_version("calmoji")
except PackageNotFoundError:  # pragma: no cover -- running from a source tree without install
    __version__ = "0.0.0+local"

__all__ = ["__version__"]
