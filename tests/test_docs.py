# tests/test_docs.py
"""The docs say what the code does: numbers from the constants, no retired file names."""

from __future__ import annotations

from pathlib import Path

import pytest

from calmoji.constants import MAX_BYTES_PER_FILE, MAX_EVENTS_PER_FILE

ROOT = Path(__file__).resolve().parent.parent
RETIRED = ("focus_weeks", "focus_all", "meeting_all", "ebi48.org")


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_readme_states_the_size_budget_from_the_constants():
    assert f"under {MAX_EVENTS_PER_FILE} events and {MAX_BYTES_PER_FILE // 1024} KB" in read("README.md")


def test_readme_covers_the_bundle_years_and_why():
    text = read("README.md")
    assert "**2026–2036**" in text
    assert "Proton accepts events only up to 2037" in text


def test_readme_has_the_upgrade_note_and_the_monthly_tips():
    text = read("README.md")
    assert "### Upgrading from v0.1.0" in text
    assert "Start with this month and next" in text
    assert "Months are in UTC" in text or "Months are in **UTC**" in text


@pytest.mark.parametrize("name", ["README.md", "docs/PLAYBOOK.md", "scripts/bundle_README.md.in"])
def test_user_docs_do_not_mention_retired_files(name):
    text = read(name)
    for old in RETIRED:
        assert old not in text, f"{name} still mentions {old}"


def test_readme_layout_trees_show_the_monthly_files():
    text = read("README.md")
    assert "focus_2026-09.ics" in text and "meetings_2026-09.ics" in text
    assert "focus_<YYYY-MM>.ics" in text and "meetings_<YYYY-MM>.ics" in text


def test_readme_no_longer_lists_the_fixed_limitations_or_roadmap_items():
    text = read("README.md")
    for gone in (
        "Meeting slot labels assume summer time",
        "appears one day a week",
        "belongs to no year",
        "emoji twice",
    ):
        assert gone not in text
    for gone in (
        "Meeting-slot labels that stay correct",
        "An EBI48 clock that appears every day",
        "leap-year gap closed",
    ):
        assert gone not in text
    for kept in ("Subscribable calendars", "calmoji.propertools.be", "Releases built automatically"):
        assert kept in text


def test_the_year_option_is_documented_as_required():
    assert "--year=YYYY          # required" in read("README.md")


def test_playbook_mentions_monthly_files_and_the_upgrade():
    text = read("docs/PLAYBOOK.md")
    assert "one file per month" in text
    assert "delete those reference" in text
