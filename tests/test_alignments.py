# tests/test_alignments.py
"""Which alignments exist, and which don't."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

import calmoji
from calmoji.calendar_config import ALIGNMENT_MODES, ALIGNMENTS, get_year_start_date
from calmoji.calendar_phases import get_semester_phases
from calmoji.cli import main, parse_args

UTC = datetime.timezone.utc
ROOT = Path(__file__).resolve().parent.parent

REAL_ALIGNMENTS = {"academic", "calendar", "fiscal_us", "fiscal_eu", "japanese_school", "indian_fiscal"}
REMOVED = ("chinese_lunar", "islamic_hijri")
TEST_ONLY = "_test_midmonth"


# -----------------------------------------------------------------------------
# The placeholder cultural alignments are gone
# -----------------------------------------------------------------------------


def test_only_the_real_alignments_are_offered():
    assert set(ALIGNMENTS) == REAL_ALIGNMENTS
    assert ALIGNMENT_MODES == REAL_ALIGNMENTS


@pytest.mark.parametrize("name", REMOVED)
def test_removed_alignments_are_not_cli_choices(name, capsys):
    with pytest.raises(SystemExit) as excinfo:
        parse_args(["--year=2027", f"--calendar-alignment={name}"])
    assert excinfo.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_help_lists_only_the_real_alignments(capsys):
    with pytest.raises(SystemExit):
        parse_args(["--help"])
    text = capsys.readouterr().out
    for name in REAL_ALIGNMENTS:
        assert name in text
    for name in (*REMOVED, TEST_ONLY):
        assert name not in text


def test_removed_alignments_are_gone_from_the_package_and_every_doc():
    package = Path(calmoji.__file__).parent
    scripts = [p for p in (ROOT / "scripts").glob("*") if p.is_file()]  # not scripts/__pycache__
    files = [*package.glob("*.py"), *ROOT.glob("*.md"), *(ROOT / "docs").glob("*.md"), *scripts]
    assert len(files) > 15
    for path in files:
        if path.name == "CHANGELOG.md":
            continue  # history may name them
        text = path.read_text(encoding="utf-8")
        for name in REMOVED:
            assert name not in text, f"{path.name} still mentions {name}"


# -----------------------------------------------------------------------------
# The test-only alignment is test-only
# -----------------------------------------------------------------------------


def test_the_test_only_alignment_is_not_public_unless_a_test_asks_for_it():
    assert TEST_ONLY not in ALIGNMENTS and TEST_ONLY not in ALIGNMENT_MODES


def test_the_test_only_alignment_works_while_injected_and_vanishes_after(midmonth_alignment):
    assert midmonth_alignment == TEST_ONLY
    assert get_year_start_date(2027, TEST_ONLY) == datetime.datetime(2027, 2, 10, tzinfo=UTC)
    assert TEST_ONLY in parse_args(["--year=2027", f"--calendar-alignment={TEST_ONLY}"]).calendar_alignment


def test_mid_month_years_fit_together(midmonth_alignment):
    for year in range(2024, 2041):
        assert get_semester_phases(year, TEST_ONLY)[-1].end == get_semester_phases(year + 1, TEST_ONLY)[0].start


def test_cli_runs_with_the_injected_alignment(midmonth_alignment, tmp_path):
    main(["--year=2027", f"--calendar-alignment={TEST_ONLY}", f"--output-dir={tmp_path / 'out'}"])
    assert (tmp_path / "out" / "seasons_2027.ics").is_file()


# -----------------------------------------------------------------------------
# Unknown alignments fail loudly
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("bad", ["acadmeic", "Academic", "", " academic", "chinese_lunar", "calendar ", "fiscal"])
def test_get_year_start_date_rejects_unknown_alignments(bad):
    with pytest.raises(ValueError) as excinfo:
        get_year_start_date(2027, bad)
    message = str(excinfo.value)
    assert repr(bad) in message  # names the bad value
    for name in sorted(REAL_ALIGNMENTS):
        assert name in message  # lists the valid ones


def test_the_error_lists_the_valid_alignments_in_order():
    with pytest.raises(
        ValueError, match="valid alignments: academic, calendar, fiscal_eu, fiscal_us, indian_fiscal, japanese_school"
    ):
        get_year_start_date(2027, "nope")


@pytest.mark.parametrize("bad", ["acadmeic", "chinese_lunar"])
def test_everything_built_on_it_raises_too(bad, tmp_path):
    from calmoji.ics_writer import write_ebi48_layer

    with pytest.raises(ValueError, match="Unknown alignment"):
        get_semester_phases(2027, bad)
    with pytest.raises(ValueError, match="Unknown alignment"):
        write_ebi48_layer(tmp_path / "x.ics", 2027, bad)
    assert not (tmp_path / "x.ics").exists()


def test_the_default_alignment_is_still_used_when_none_is_given():
    assert get_year_start_date(2027) == datetime.datetime(2027, 9, 1, tzinfo=UTC)
    assert get_semester_phases(2027)[0].start == datetime.datetime(2027, 9, 1, tzinfo=UTC)


def test_every_real_alignment_still_resolves():
    for name in REAL_ALIGNMENTS:
        assert get_year_start_date(2027, name).year == 2027


def test_no_other_alignment_lookup_falls_back_silently():
    # the only place that resolves an alignment name is get_year_start_date; nothing else defaults it
    package = Path(calmoji.__file__).parent
    for path in package.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "ALIGNMENTS.get(" not in text, path.name
