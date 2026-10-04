# tests/test_docs.py
"""The docs say what the code does: numbers from the constants, no retired file names."""

from __future__ import annotations

from pathlib import Path

import pytest

from calmoji.constants import MAX_BYTES_PER_FILE, MAX_EVENTS_PER_FILE

ROOT = Path(__file__).resolve().parent.parent
RETIRED = ("focus_weeks", "focus_all", "meeting_all", "ebi48.org")

# Old layer and group names: gone from everything a person reads. (Code identifiers such as
# get_semester_phases, and the CHANGELOG's history, may keep them.)
OLD_NAMES = (
    "semester_phases_",
    "ebi48_layer_",
    "Semester Phases",
    "Semester phases",
    "Focus Blocks",
    "Meeting Slots",
    "EBI48 Clock",
    "EBI48 clock",
    "Other People's Stuff",
    "🧾 Deadlines",
    "Reference layers",
    "reference layers",
    "Working calendars",
    "working calendars",
    "(immutable)",
    "(mutable)",
    "Colours matter",
)
USER_FACING = ["README.md", "docs/PLAYBOOK.md", "scripts/bundle_README.md.in", "EBI48-README.md"]


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
    assert "delete those Map" in text


# -----------------------------------------------------------------------------
# Layer names, groups, colours
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("name", USER_FACING)
def test_no_old_layer_name_remains_in_user_facing_text(name):
    text = read(name)
    for old in OLD_NAMES:
        assert old not in text, f"{name} still says {old!r}"


def test_the_new_layer_names_are_used():
    for name in ("README.md", "docs/PLAYBOOK.md", "scripts/bundle_README.md.in"):
        text = read(name)
        for layer in ("🌗 Seasons", "🧠 Focus — Open", "🕒 Meetings — Open", "🧿 Emoji Clock"):
            assert layer in text, f"{name} lacks {layer}"
    assert "seasons_2026.ics" in read("README.md") and "emoji_clock_2026.ics" in read("README.md")
    assert "seasons_<year>.ics" in read("scripts/bundle_README.md.in")


def test_playbook_groups_summary_and_tags():
    text = read("docs/PLAYBOOK.md")
    assert "*The Map shows what's possible; Commitments hold what you've chosen.*" in text
    for heading in ("### The Map (toggle on to plan, off to work)", "### Commitments", "### Life", "### Sandbox"):
        assert heading in text
    assert "`(read-only)`" in text and "`(mine)`" in text
    assert "🪷 Feast Days | Birthdays, anniversaries, days worth marking" in text
    for renamed in ("🫂 For Others", "⚖️ Hard Deadlines"):
        assert renamed in text
    # the Emoji Clock is introduced as built on EBI48, with a link
    assert "built on EBI48; see [EBI48-README.md](../EBI48-README.md)" in text


EXPECTED_PALETTE = {
    "🌗 Seasons": ("Fern", "#63B84E"),
    "🧠 Focus — Open": ("Soil", "#524740"),
    "🕒 Meetings — Open": ("Forest", "#448533"),
    "🧿 Emoji Clock": ("Cobalt", "#2C3DAB"),
    "🎯 Focus — Claimed": ("Ocean", "#3575A2"),
    "🤝 Meetings — One-off": ("Pacific", "#4A9DD4"),
    "🔄 Meetings — Recurring": ("Ocean", "#3575A2"),
    "🛠️ Everyday Stuff": ("Purple", "#8080F7"),
    "🫂 For Others": ("Pink", "#CC67D0"),
    "👨‍👩‍👧 Family": ("Rose", "#DA4D7C"),
    "✈️ Travel": ("Carrot", "#E88A33"),
    "🪷 Feast Days": ("Cobalt", "#2C3DAB"),
    "⚖️ Hard Deadlines": ("Raspberry", "#AB2F56"),
    "🧪 Sandbox": ("Olive", "#7E7323"),
}


def test_the_colour_table_matches_the_palette():
    text = read("docs/PLAYBOOK.md")
    section = text[text.index("\n## Colours\n") : text.index("\n## Setting it up\n")]
    rows = {}
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[2].startswith("`#"):
            rows[cells[0]] = (cells[1], cells[2].strip("`"))
    assert rows == EXPECTED_PALETTE


def test_colours_is_a_plain_heading_so_the_anchor_resolves_on_github():
    playbook = read("docs/PLAYBOOK.md").splitlines()
    assert playbook.count("## Colours") == 1
    # GitHub's anchor for "## Colours" is "#colours" (lowercased, no suffix) as long as no other
    # heading slugs the same way.
    slugs = [line.lstrip("#").strip().lower().replace(" ", "-") for line in playbook if line.startswith("#")]
    assert slugs.count("colours") == 1
    assert "[calm starting palette](docs/PLAYBOOK.md#colours)" in read("README.md")


def test_the_colours_section_follows_the_sandbox_table_and_the_rule_comes_before_the_weekly_loop():
    text = read("docs/PLAYBOOK.md")
    assert text.index("### Sandbox") < text.index("\n## Colours\n") < text.index("\n## Setting it up\n")
    assert text.index("\n## The rule underneath\n") < text.index("\n## The weekly loop\n")
    assert text.index("\n## Setting it up\n") < text.index("\n## The rule underneath\n")


def test_the_rule_underneath_is_in_trey_s_words():
    text = read("docs/PLAYBOOK.md")
    assert "A to-do list is a promise without a time" in text
    assert "* **Trivial? Do it today.**" in text
    assert "* **A future commitment? Give it a time.** Claim an open focus block for it, so" in text
    assert "**hyperfocus becomes visible.**" in text


def test_the_emoji_clock_section_and_where_ebi48_came_from():
    readme = read("README.md")
    section = readme[readme.index("### 🧿 Emoji Clock") : readme.index("### ⚠️ Known limitations")]
    assert "I designed EBI48 after years of watching global technical standards" in section
    assert "**pick a day and look for free animals at acceptable\ntimes**" in section
    assert "See [EBI48-README.md](EBI48-README.md)." in section

    ebi48 = read("EBI48-README.md")
    assert ebi48.index("## 🗣 Where it came from") < ebi48.index("## 🧭 Why It Exists")
    assert "**pick a day,\nfind free animals at acceptable times.**" in ebi48


def test_bundle_readme_and_readme_explain_that_every_time_is_utc():
    assert "Every time in these files is in **UTC**" in read("scripts/bundle_README.md.in")
    assert "All times are fixed in **UTC**; your calendar app shows them in your" in read("README.md")
