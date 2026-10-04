#!/usr/bin/env python3
"""
calmoji.py — legacy script entry point.

The implementation lives in :mod:`calmoji.cli`. This shim is kept so that
existing ``python3 calmoji.py --year=2039`` invocations continue to work after
the move to a proper installable package.

Prefer the installed entry points:

    calmoji --year=2039
    python -m calmoji --year=2039
"""

from __future__ import annotations

from calmoji.cli import main

if __name__ == "__main__":
    main()
