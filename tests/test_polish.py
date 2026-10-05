# tests/test_polish.py
"""Least-surprise polish: constant calendar names, one reference link, --year required, no repeated emoji."""

from __future__ import annotations

import re
from collections import defaultdict

import pytest

from calmoji.cli import main, parse_args
from calmoji.constants import CALNAME_EBI48, CALNAME_FOCUS, CALNAME_MEETINGS, CALNAME_PHASES, EBI48_URL
from tests.ics_helpers import header_lines, read_events

EXPECTED_NAMES = {
    "phases": "🌗 Seasons",
    "focus": "🧠 Focus — Open",
    "meetings": "🕒 Meetings — Open",
    "ebi48": "🧿 Emoji Clock",
}


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    """Two years of two alignments, with Oceania so that every kind of event is present."""
    root = tmp_path_factory.mktemp("polish")
    for alignment in ("academic", "calendar"):
        for year in (2027, 2028):
            main(
                [
                    f"--year={year}",
                    f"--calendar-alignment={alignment}",
                    f"--output-dir={root / alignment / str(year)}",
                    "--include-oceania",
                ]
            )
    return root


def layer_of(path) -> str:
    if path.name.startswith("seasons_"):
        return "phases"
    if path.name.startswith("emoji_clock_"):
        return "ebi48"
    return path.parent.name  # focus / meetings


def test_the_constants_are_the_agreed_names():
    assert (CALNAME_PHASES, CALNAME_FOCUS, CALNAME_MEETINGS, CALNAME_EBI48) == tuple(
        EXPECTED_NAMES[k] for k in ("phases", "focus", "meetings", "ebi48")
    )


def test_every_file_of_a_layer_has_the_same_calendar_name_with_no_year_date_or_phase(generated):
    names = defaultdict(set)
    files = sorted(generated.rglob("*.ics"))
    assert len(files) > 100
    for path in files:
        header = header_lines(path)
        calname = next(line for line in header if line.startswith("X-WR-CALNAME:")).split(":", 1)[1]
        assert f"NAME:{calname}" in header
        assert "UTC" not in calname and "(" not in calname, f"{path.name}: {calname!r}"
        names[layer_of(path)].add(calname)
        assert not re.search(r"\d", calname.replace("EBI48", "")), f"{path.name}: {calname!r} carries a year or date"

    assert {layer: sorted(found) for layer, found in names.items()} == {
        layer: [name] for layer, name in EXPECTED_NAMES.items()
    }


def test_no_generated_file_mentions_ebi48_org(generated):
    for path in generated.rglob("*.ics"):
        assert "ebi48.org" not in path.read_bytes().decode("utf-8").replace("\r\n ", ""), path.name


def test_the_ebi48_reference_link_is_the_github_readme_and_defined_once():
    assert EBI48_URL == "https://github.com/propertools/Calmoji-Forge/blob/main/EBI48-README.md"
    from pathlib import Path

    import calmoji

    package = Path(calmoji.__file__).parent
    definitions = [
        p.name
        for p in package.glob("*.py")
        if "github.com/propertools/Calmoji-Forge/blob/main" in p.read_text(encoding="utf-8")
    ]
    assert definitions == ["constants.py"]


def test_year_is_required(capsys):
    with pytest.raises(SystemExit) as excinfo:
        parse_args([])
    assert excinfo.value.code == 2
    assert "--year" in capsys.readouterr().err

    with pytest.raises(SystemExit):
        parse_args(["--calendar-alignment=calendar"])

    assert parse_args(["--year=2030"]).year == 2030


# An emoji is a symbol or pictograph; variation selectors and joiners are not counted.
EMOJI_RANGES = ((0x1F000, 0x1FFFF), (0x2600, 0x27BF), (0x2B00, 0x2BFF))


def emojis_in(text: str):
    return [c for c in text if any(lo <= ord(c) <= hi for lo, hi in EMOJI_RANGES)]


def test_the_emoji_finder_finds_emoji_and_ignores_punctuation():
    assert emojis_in("🐶 Dog Face — EBI48") == ["🐶"]
    assert emojis_in("🐶 🐶 Dog Face") == ["🐶", "🐶"]
    assert emojis_in("❄️ Winter Break → 🌾") == ["❄", "🌾"]
    assert emojis_in("Focus Block 1 — Semester A — 2027-W49") == []


def test_no_summary_contains_the_same_emoji_twice(generated):
    checked = 0
    for path in sorted(generated.rglob("*.ics")):
        for event in read_events(path):
            found = emojis_in(event["SUMMARY"])
            assert len(found) == len(set(found)), f"{path.name}: {event['SUMMARY']!r}"
            checked += 1
    assert checked > 5000


def test_generated_files_use_the_new_file_names(generated):
    for year_dir in sorted(p for p in generated.glob("*/*") if p.is_dir()):
        year = year_dir.name
        assert (year_dir / f"seasons_{year}.ics").is_file()
        assert (year_dir / f"emoji_clock_{year}.ics").is_file()
        assert not list(year_dir.glob("semester_phases_*")) and not list(year_dir.glob("ebi48_layer_*"))


KEY = "\U0001f5dd"  # the old marker's emoji; the variation selector after it doesn't matter here


def test_no_generated_file_in_any_layer_contains_a_glyph_key(generated):
    """The 🗝️ Glyph Key events were retired in v0.1.3: not in Seasons, Focus, Meetings or the Emoji Clock."""
    layers = defaultdict(int)
    for path in sorted(generated.rglob("*.ics")):
        text = path.read_bytes().decode("utf-8").replace("\r\n ", "")  # unfold
        assert "Glyph Key" not in text, f"{path.name} mentions a Glyph Key"
        assert KEY not in text, f"{path.name} contains the key emoji"
        layers[layer_of(path)] += 1

    # all four layers were really scanned
    assert set(layers) == {"phases", "focus", "meetings", "ebi48"}


def test_the_code_no_longer_builds_glyph_keys():
    from pathlib import Path

    import calmoji

    for source in Path(calmoji.__file__).parent.glob("*.py"):
        text = source.read_text(encoding="utf-8")
        assert "Glyph Key" not in text and KEY not in text, source.name
