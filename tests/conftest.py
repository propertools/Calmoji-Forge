# tests/conftest.py

"""Shared fixtures."""

from __future__ import annotations

from typing import Iterator

import pytest

from tests.alignment_helpers import injected_midmonth


@pytest.fixture
def midmonth_alignment() -> Iterator[str]:
    """The test-only mid-month alignment (see tests/alignment_helpers.py), for one test."""
    with injected_midmonth() as name:
        yield name
