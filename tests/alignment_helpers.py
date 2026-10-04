# tests/alignment_helpers.py

"""A test-only alignment, injected for as long as a test (or module) needs it."""

from __future__ import annotations

import datetime
from contextlib import contextmanager
from typing import Iterator

from calmoji import calendar_config

UTC = datetime.timezone.utc

MIDMONTH = "_test_midmonth"


@contextmanager
def injected_midmonth() -> Iterator[str]:
    """
    Register a test-only alignment whose year starts mid-month, on 10 February.

    It covers what the removed placeholder alignments used to: years whose edge months are
    partial, with the rest of the month in the neighbouring year's folder. It is registered
    only inside the `with` block, so it never appears in the package's public list or in --help.
    """
    calendar_config.ALIGNMENTS[MIDMONTH] = lambda year: datetime.datetime(year, 2, 10, tzinfo=UTC)
    calendar_config.ALIGNMENT_MODES.add(MIDMONTH)
    try:
        yield MIDMONTH
    finally:
        calendar_config.ALIGNMENTS.pop(MIDMONTH, None)
        calendar_config.ALIGNMENT_MODES.discard(MIDMONTH)
