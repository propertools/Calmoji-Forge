# tests/test_docs.py
"""The docs say what the code does: numbers from the constants, no retired file names."""

from __future__ import annotations

import re
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


# -----------------------------------------------------------------------------
# v0.1.2: docs that say only true things
# -----------------------------------------------------------------------------


def test_readme_does_not_claim_preflight_runs_every_ci_check():
    text = " ".join(read("README.md").split())
    assert "runs every check CI runs" not in text
    assert "runs CI's main checks on your machine" in text
    assert (
        "CI also tests Python 3.9 through 3.13, compares output across Python versions, "
        "and runs on macOS's `/usr/bin/python3`" in text
    )


def test_the_download_is_named_by_pattern_so_it_needs_no_edit_each_release():
    assert "calmoji-artifacts-vX.Y.Z.zip" in read("README.md")
    assert "releases/latest" in read("README.md")
    for name in ("README.md", "scripts/bundle_README.md.in"):
        assert not re.search(r"calmoji-artifacts-v\d", read(name)), f"{name} names a specific release"


def test_readme_documents_the_output_folder_and_the_rerun_rule():
    text = " ".join(read("README.md").split())
    assert "output/<year>/<alignment>/" in text
    assert ".calmoji-output" in text
    assert "re-running replaces its own files" in text
    assert "refused, untouched" in text
    assert "--output-dir=DIR     # default: output/<year>/<alignment>/" in read("README.md")


def test_readme_says_dtstamp_is_a_fixed_documented_constant():
    text = " ".join(read("README.md").split())
    assert "`DTSTAMP`" in text and "fixed, documented constant" in text and "files stay reproducible" in text


def test_the_dtstamp_constant_is_explained_next_to_it():
    source = read("calmoji/constants.py")
    comment = source[: source.index("DTSTAMP =")]
    assert "fixed, documented constant" in comment and "reproducible" in comment


def test_contributing_roadmap_no_longer_lists_finished_work():
    text = read("CONTRIBUTING.md")
    roadmap = text[text.index("# 🔧 Roadmap") : text.index("# 🧪 Testing Standards")]
    for done in (
        "`--output-dir` override",
        "`--dry-run` enforcement tests",
        "`--version` flag",
        "--calendar-mode",
        "Combined vs per-phase",
        "Explicit output directory validation",
    ):
        assert done not in roadmap, done
    for open_item in ("Optional config file", "Atomic file writes", "structured logging"):
        assert open_item in roadmap, open_item


def test_the_coverage_claim_is_enforced():
    pyproject = read("pyproject.toml")
    section = pyproject[pyproject.index("[tool.coverage.report]") :]
    assert re.search(r"^fail_under = 90\b", section, re.M)
    assert "Coverage threshold ≥ 90%" in read("CONTRIBUTING.md")


def test_test_strategy_claims_only_what_is_implemented():
    text = read("TEST_STRATEGY.md")
    assert "Codecov" not in text
    assert "coverage.xml" in text  # what CI actually does
    assert "**targets**, not gates" in text
    for unimplemented in (
        "Any critical deterministic module drops below",
        "Branch coverage regresses",
        "rely on local timezone",
    ):
        assert unimplemented not in text
    assert "fail_under" in text and "90%" in text


def test_ci_really_measures_coverage_so_fail_under_applies():
    ci = read(".github/workflows/ci.yml")
    assert "--cov=calmoji" in ci and "--cov-branch" in ci


# -----------------------------------------------------------------------------
# The optional AI agenda steward
# -----------------------------------------------------------------------------

STEWARD_HEADING = "## Optional: an AI agenda steward"


def github_slug(heading: str) -> str:
    """GitHub's heading anchor: lowercase, punctuation dropped, spaces to hyphens."""
    text = heading.lstrip("#").strip().lower()
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def test_the_steward_section_ends_the_playbook_and_its_code_block_is_closed():
    text = read("docs/PLAYBOOK.md")
    lines = text.splitlines()
    assert lines.count(STEWARD_HEADING) == 1
    section = text[text.index(STEWARD_HEADING) :]
    assert section.rstrip().endswith("become more machine-like.\n```")
    assert section.count("```") == 2  # one block, opened and closed
    assert text.count("```") % 2 == 0  # no fence left open anywhere in the playbook
    assert "```text\nYou're my agenda steward. I plan my time with calmoji." in section


def test_the_steward_prompt_uses_the_current_layer_names():
    section = read("docs/PLAYBOOK.md")
    section = section[section.index(STEWARD_HEADING) :]
    for name in ("🌗 Seasons", "🧠 Focus — Open", "🕒 Meetings — Open", "🧿 Emoji Clock", "🎯 Focus — Claimed"):
        assert name in section, name
    assert "calmoji needs no AI, no account and no cloud service" in section
    assert "Never make commitments, cancel plans, contact anyone or change my calendar" in section


def test_the_readme_points_at_the_steward_section_and_the_anchor_resolves():
    readme = read("README.md")
    how_to_use = readme[readme.index("## 🧭 How to use it") : readme.index("## 🗂 What's in each layer")]
    assert (
        "Prefer to plan with an AI assistant? See the\n[playbook](docs/PLAYBOOK.md#optional-an-ai-agenda-steward)."
        in how_to_use
    )

    headings = [line for line in read("docs/PLAYBOOK.md").splitlines() if line.startswith("#")]
    slugs = [github_slug(h) for h in headings]
    assert slugs.count("optional-an-ai-agenda-steward") == 1
    assert github_slug(STEWARD_HEADING) == "optional-an-ai-agenda-steward"


def test_the_v0_1_3_todos_are_done_and_no_longer_listed():
    readme = " ".join(read("README.md").split())
    contributing = " ".join(read("CONTRIBUTING.md").split())

    assert "Small fixes planned for v0.1.3" not in readme
    assert "**v0.1.3:**" not in contributing
    assert "`unfold_ics_lines`) splits lines on more characters" not in readme
    # the roadmap items that are still open are still there
    assert "Subscribable calendars" in readme and "Atomic file writes" in contributing


# -----------------------------------------------------------------------------
# Where macOS's python3 really comes from (v0.1.3)
# -----------------------------------------------------------------------------

OLD_MACOS_WORDING = (
    "ships with macOS",
    "ship with macOS",
    "stock macOS",
    "stock Mac",
    "macOS ships",
    "every Mac already has",
)


@pytest.mark.parametrize(
    "name",
    [
        "README.md",
        "TEST_STRATEGY.md",
        "CONTRIBUTING.md",
        ".github/workflows/ci.yml",
        "scripts/bundle_README.md.in",
        "docs/PLAYBOOK.md",
    ],
)
def test_no_file_claims_python_ships_with_macos(name):
    text = " ".join(read(name).split())
    for old in OLD_MACOS_WORDING:
        assert old not in text, f"{name} still says {old!r}"


def test_readme_says_the_python3_comes_from_apples_command_line_tools():
    text = " ".join(read("README.md").split())
    assert (
        "including the `python3` from Apple's Command Line Tools (a Mac offers to install them the first time you run `python3`)"
        in text
    )
    assert "upgrade pip first (the pip that comes with Apple's Python is old)" in text
    assert "runs on macOS's `/usr/bin/python3`" in text


def test_the_ci_job_is_named_for_what_it_really_tests():
    ci = read(".github/workflows/ci.yml")
    assert "name: macOS /usr/bin/python3" in ci
    assert "stock macOS python3" not in ci and "stock-macos" not in ci
    assert "Apple's Command Line Tools" in ci
    assert "/usr/bin/python3 calmoji.py --year=2030" in ci  # and it still runs that interpreter


def test_test_strategy_names_the_macos_interpreter_exactly():
    assert "on macOS's `/usr/bin/python3`" in read("TEST_STRATEGY.md")


def test_readme_says_calmoji_recognises_its_own_files_by_name():
    text = " ".join(read("README.md").split())
    assert (
        "calmoji recognises its own files by name. Anything else in its folder, including another `.ics` file, makes it refuse without deleting anything."
        in text
    )
    assert "refused, untouched" in text
    assert "re-running replaces its own files" in text


def test_the_bundle_readme_template_makes_no_claim_about_deleting_calmojis_folder():
    text = read("scripts/bundle_README.md.in")
    assert "deletes" not in text and "recognises its own files" not in text
    assert "--exclude=.calmoji-output" in text  # the marker is still explained where it matters
