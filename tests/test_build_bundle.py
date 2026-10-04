# tests/test_build_bundle.py
"""
Tests for scripts/build_bundle.py, the release-archive builder.

The script lives outside the package, so it is loaded by path. Bundles are built
for a couple of years only; scripts/preflight.sh builds two years (2026-2027),
and only the release process runs the full 2026-2039 build.
"""

from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import importlib.util
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

import calmoji
from calmoji.cli import main as calmoji_main
from calmoji.constants import MAX_BYTES_PER_FILE, MAX_EVENTS_PER_FILE
from calmoji.ics_writer import IcsBudgetError

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "build_bundle.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("build_bundle", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_bundle"] = module
    spec.loader.exec_module(module)
    return module


bb = _load_script()

VERSION = calmoji.__version__
YEARS = [2027, 2028]
ALIGNMENTS = ["academic", "calendar"]

# The script reads the version from installed package metadata and refuses to run without it.
needs_install = pytest.mark.skipif("+local" in VERSION, reason="calmoji is not pip-installed in this environment")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """Two independent builds of the same small bundle."""
    first = bb.build_bundle(tmp_path_factory.mktemp("bundle-a"), YEARS, ALIGNMENTS)
    second = bb.build_bundle(tmp_path_factory.mktemp("bundle-b"), YEARS, ALIGNMENTS)
    return first, second


# -----------------------------------------------------------------------------
# --years / --alignments
# -----------------------------------------------------------------------------


def test_parse_years_range_is_inclusive():
    assert bb.parse_years("2026-2039") == list(range(2026, 2040))


def test_parse_years_single_year():
    assert bb.parse_years("2030") == [2030]
    assert bb.parse_years("2030-2030") == [2030]


@pytest.mark.parametrize("spec", [" 2026-2028 ", "2026 - 2028", "2026–2028"])
def test_parse_years_tolerates_spaces_and_en_dash(spec):
    assert bb.parse_years(spec) == [2026, 2027, 2028]


@pytest.mark.parametrize(
    "spec",
    [
        "",
        "abc",
        "2026-",
        "-2030",
        "2026-2030-2035",
        "2026,2028",
        "202-2030",
        "20260-2030",
        "2039-2026",  # reversed
        "1899-1900",  # below the supported window
        "2026-2101",  # above it (a typo guard)
    ],
)
def test_parse_years_rejects_bad_input(spec):
    with pytest.raises(argparse.ArgumentTypeError):
        bb.parse_years(spec)


def test_default_years_cover_the_published_range():
    assert bb.parse_years(bb.DEFAULT_YEARS) == list(range(2026, 2040))


def test_parse_alignments():
    assert bb.parse_alignments("academic,calendar") == ["academic", "calendar"]
    assert bb.parse_alignments("calendar") == ["calendar"]
    assert bb.parse_alignments(" calendar , academic ") == ["calendar", "academic"]
    assert bb.parse_alignments("academic,academic,calendar") == ["academic", "calendar"]


@pytest.mark.parametrize("spec", ["", ",", "academic,", "academic,,calendar", "klingon", "academic,klingon"])
def test_parse_alignments_rejects_bad_input(spec):
    with pytest.raises(argparse.ArgumentTypeError):
        bb.parse_alignments(spec)


def test_main_rejects_invalid_years(tmp_path, capsys):
    with pytest.raises(SystemExit) as excinfo:
        bb.main(["--out", str(tmp_path), "--years", "2039-2026"])

    assert excinfo.value.code == 2
    assert "2039 is after 2026" in capsys.readouterr().err
    assert not list(tmp_path.iterdir())


def test_main_refuses_an_uninstalled_calmoji(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(bb, "__version__", "0.0.0+local")

    assert bb.main(["--out", str(tmp_path), "--years", "2027", "--alignments", "academic"]) == 1

    assert "not installed" in capsys.readouterr().err
    assert not list(tmp_path.iterdir())


# -----------------------------------------------------------------------------
# Layout
# -----------------------------------------------------------------------------


def _tree(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_bundle_layout_matches_the_cli(built, tmp_path):
    result, _ = built
    for year in YEARS:
        for alignment in ALIGNMENTS:
            cli_dir = tmp_path / str(year) / alignment
            calmoji_main([f"--year={year}", f"--calendar-alignment={alignment}", f"--output-dir={cli_dir}"])

            # same files, same bytes, in the CLI's own monthly layout
            assert _tree(result.bundle_dir / str(year) / alignment) == _tree(cli_dir)


def test_bundle_year_folders_use_the_monthly_layout(built):
    result, _ = built
    year_dir = result.bundle_dir / "2027" / "academic"
    names = sorted(p.relative_to(year_dir).as_posix() for p in year_dir.rglob("*.ics"))
    assert "semester_phases_2027.ics" in names and "ebi48_layer_2027.ics" in names
    assert "focus/focus_2027-09.ics" in names and "meetings/meetings_2028-08.ics" in names
    assert not any(n.startswith(("focus_all", "meeting_all", "focus_weeks")) for n in names)


def test_bundle_folder_is_named_after_the_version(built):
    result, _ = built
    assert result.version == VERSION
    assert result.bundle_dir.name == f"v{VERSION}"
    assert result.zip_path.name == f"calmoji-artifacts-v{VERSION}.zip"
    assert result.tar_path.name == f"calmoji-artifacts-v{VERSION}.tar.gz"


def test_rebuilding_does_not_keep_stale_files(tmp_path):
    bb.build_bundle(tmp_path, [2027], ["academic"])
    stale = tmp_path / f"v{VERSION}" / "2027" / "academic" / "stale.ics"
    stale.write_text("not a calendar", encoding="utf-8")

    result = bb.build_bundle(tmp_path, [2027], ["academic"])

    assert not stale.exists()
    assert "stale.ics" not in (result.bundle_dir / bb.MANIFEST_NAME).read_text(encoding="utf-8")


def test_stray_file_is_refused(tmp_path):
    result = bb.build_bundle(tmp_path, [2027], ["academic"])
    (result.bundle_dir / ".DS_Store").write_bytes(b"\x00")

    with pytest.raises(ValueError, match=r"unexpected file in bundle: \.DS_Store"):
        bb.archive_entries(result.bundle_dir)


# -----------------------------------------------------------------------------
# MANIFEST.sha256
# -----------------------------------------------------------------------------

MANIFEST_LINE = re.compile(r"^[0-9a-f]{64}  \./\S+\.ics$")


def test_manifest_format(built):
    result, _ = built
    raw = (result.bundle_dir / bb.MANIFEST_NAME).read_bytes()

    assert raw.endswith(b"\n")
    assert b"\r" not in raw
    lines = raw.decode("utf-8").splitlines()
    assert lines, "manifest is empty"
    assert all(MANIFEST_LINE.match(line) for line in lines), "every line is '<sha256>  ./<path>.ics'"

    paths = [line.split("  ", 1)[1] for line in lines]
    assert paths == sorted(paths), "sorted by path"
    assert len(paths) == len(set(paths))
    assert len(lines) == result.ics_count


def test_manifest_lists_exactly_the_ics_files_with_correct_hashes(built):
    result, _ = built
    on_disk = {"./" + p.relative_to(result.bundle_dir).as_posix(): p for p in result.bundle_dir.rglob("*.ics")}

    listed = {}
    for line in (result.bundle_dir / bb.MANIFEST_NAME).read_text(encoding="utf-8").splitlines():
        digest, path = line.split("  ", 1)
        listed[path] = digest

    assert set(listed) == set(on_disk)
    for path, digest in listed.items():
        assert digest == hashlib.sha256(on_disk[path].read_bytes()).hexdigest()
    assert len(on_disk) == result.ics_count


@pytest.mark.skipif(
    shutil.which("shasum") is None and shutil.which("sha256sum") is None, reason="no shasum or sha256sum available"
)
def test_manifest_verifies_with_the_system_tools(built, tmp_path):
    result, _ = built
    with zipfile.ZipFile(result.zip_path) as zf:
        zf.extractall(tmp_path)
    folder = tmp_path / f"v{VERSION}"

    commands = []
    if shutil.which("shasum"):
        commands.append(["shasum", "-a", "256", "-c", bb.MANIFEST_NAME])
    if shutil.which("sha256sum"):
        commands.append(["sha256sum", "-c", bb.MANIFEST_NAME])
    for command in commands:
        done = subprocess.run(command, cwd=folder, capture_output=True, text=True)
        assert done.returncode == 0, f"{command[0]}: {done.stdout[-300:]} {done.stderr[-300:]}"
        checked = [line for line in done.stdout.splitlines() if line.endswith(": OK")]
        assert len(checked) == result.ics_count


# -----------------------------------------------------------------------------
# README
# -----------------------------------------------------------------------------


def test_readme_is_filled_in_for_per_phase_focus_files(built):
    result, _ = built
    text = (result.bundle_dir / bb.README_NAME).read_text(encoding="utf-8")

    assert f"v{VERSION}" in text
    assert "2027–2028" in text
    assert not re.search(r"@[A-Z][A-Z_]*@", text), "unfilled placeholder"

    assert "focus_all_<year>.ics" in text
    assert "focus_<phase>_<from>_to_<to>.ics" in text
    for gone in ("focus_weeks", "ISO week", "week number", "W49", "Weeks at phase boundaries"):
        assert gone not in text, f"stale per-week advice: {gone!r}"


def test_render_readme_substitutions_and_leftover_placeholders():
    assert bb.render_readme("v@VERSION@ @YEARS@", "9.9.9", [2030]) == "v9.9.9 2030"
    assert bb.render_readme("@YEARS@ @VERSION@", "1.2.3", [2026, 2027, 2028]) == "2026–2028 1.2.3"
    with pytest.raises(ValueError, match="@NOPE@"):
        bb.render_readme("@VERSION@ @NOPE@", "1.2.3", [2030])


# -----------------------------------------------------------------------------
# Deterministic archives
# -----------------------------------------------------------------------------


def test_two_builds_produce_byte_identical_archives(built):
    first, second = built
    assert first.zip_path.read_bytes() == second.zip_path.read_bytes()
    assert first.tar_path.read_bytes() == second.tar_path.read_bytes()
    assert (first.zip_sha256, first.tar_sha256) == (second.zip_sha256, second.tar_sha256)


def test_rebuilding_into_the_same_directory_gives_identical_archives(tmp_path):
    first = bb.build_bundle(tmp_path, [2027], ["calendar"])
    zip_bytes, tar_bytes = first.zip_path.read_bytes(), first.tar_path.read_bytes()

    second = bb.build_bundle(tmp_path, [2027], ["calendar"])

    assert second.zip_path.read_bytes() == zip_bytes
    assert second.tar_path.read_bytes() == tar_bytes


def test_reported_checksums_are_those_of_the_files(built):
    result, _ = built
    assert result.zip_sha256 == hashlib.sha256(result.zip_path.read_bytes()).hexdigest()
    assert result.tar_sha256 == hashlib.sha256(result.tar_path.read_bytes()).hexdigest()


def _expected_names(result) -> list:
    """Independent expectation: the folder, its subfolders and files, sorted by path."""
    root = result.bundle_dir.parent
    return sorted([result.bundle_dir.name] + [p.relative_to(root).as_posix() for p in result.bundle_dir.rglob("*")])


def test_zip_entries_are_sorted_and_normalised(built):
    result, _ = built
    with zipfile.ZipFile(result.zip_path) as zf:
        infos = zf.infolist()
        assert zf.testzip() is None
        assert zf.comment == b""

        assert [i.filename.rstrip("/") for i in infos] == _expected_names(result)
        assert infos[0].filename == f"v{VERSION}/"

        for info in infos:
            assert info.date_time == (1980, 1, 1, 0, 0, 0), info.filename
            assert info.create_system == 3, info.filename
            assert info.extra == b"" and info.comment == b"", info.filename
            if info.is_dir():
                assert info.external_attr >> 16 == 0o40755, info.filename
            else:
                assert info.compress_type == zipfile.ZIP_DEFLATED, info.filename
                assert info.external_attr >> 16 == 0o100644, info.filename
                assert zf.read(info) == (result.bundle_dir.parent / info.filename).read_bytes()


def test_tar_entries_are_sorted_and_normalised(built):
    result, _ = built
    with tarfile.open(result.tar_path, mode="r:gz") as tar:
        members = tar.getmembers()

        assert [m.name for m in members] == _expected_names(result)
        assert members[0].name == f"v{VERSION}"

        for member in members:
            assert (member.mtime, member.uid, member.gid) == (0, 0, 0), member.name
            assert (member.uname, member.gname) == ("", ""), member.name
            assert not member.pax_headers, member.name
            if member.isdir():
                assert member.mode == 0o755, member.name
            else:
                assert member.isreg() and member.mode == 0o644, member.name
                extracted = tar.extractfile(member)
                assert extracted is not None
                assert extracted.read() == (result.bundle_dir.parent / member.name).read_bytes()


def test_gzip_header_has_no_time_and_no_file_name(built):
    result, _ = built
    header = result.tar_path.read_bytes()[:10]

    assert header[:3] == b"\x1f\x8b\x08"  # gzip, deflate
    assert header[3] == 0, "FLG: no FNAME, FEXTRA, FCOMMENT or FHCRC"
    assert header[4:8] == b"\x00\x00\x00\x00", "MTIME is 0"
    with gzip.open(result.tar_path) as handle:
        assert handle.read(512)[:6] == f"v{VERSION}".encode()


def test_both_archives_hold_the_same_files(built):
    result, _ = built
    with zipfile.ZipFile(result.zip_path) as zf:
        zip_files = {i.filename: zf.read(i) for i in zf.infolist() if not i.is_dir()}
    with tarfile.open(result.tar_path, mode="r:gz") as tar:
        tar_files = {}
        for member in tar.getmembers():
            if member.isreg():
                handle = tar.extractfile(member)
                assert handle is not None
                tar_files[member.name] = handle.read()

    assert zip_files == tar_files
    assert f"v{VERSION}/{bb.MANIFEST_NAME}" in zip_files
    assert f"v{VERSION}/{bb.README_NAME}" in zip_files
    assert len(zip_files) == result.file_count


# -----------------------------------------------------------------------------
# Command line
# -----------------------------------------------------------------------------


@needs_install
def test_main_prints_file_count_sizes_and_checksums(tmp_path, capsys):
    assert bb.main(["--out", str(tmp_path), "--years", "2027", "--alignments", "academic"]) == 0
    shown = capsys.readouterr().out

    zip_path = tmp_path / f"calmoji-artifacts-v{VERSION}.zip"
    tar_path = tmp_path / f"calmoji-artifacts-v{VERSION}.tar.gz"
    ics_count = len(list((tmp_path / f"v{VERSION}").rglob("*.ics")))
    assert f"Files: {ics_count} .ics (+ {bb.MANIFEST_NAME} and {bb.README_NAME}: {ics_count + 2} files in all)" in shown
    for path in (zip_path, tar_path):
        assert f"{path.name}: {path.stat().st_size:,} bytes" in shown
        assert f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" in shown


@needs_install
def test_script_runs_as_a_program(tmp_path):
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(tmp_path), "--years", "2027", "--alignments", "calendar"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )

    assert done.returncode == 0, done.stderr
    assert (tmp_path / f"calmoji-artifacts-v{VERSION}.zip").is_file()
    assert (tmp_path / f"calmoji-artifacts-v{VERSION}.tar.gz").is_file()
    assert (tmp_path / f"v{VERSION}" / "2027" / "calendar" / "focus" / "focus_2027-01.ics").is_file()


# -----------------------------------------------------------------------------
# Hygiene
# -----------------------------------------------------------------------------

# Anything that could smuggle the clock, the host, the user or randomness into the output.
NONDETERMINISTIC_MODULES = {
    "time",
    "datetime",
    "random",
    "secrets",
    "uuid",
    "socket",
    "getpass",
    "platform",
    "tempfile",
    "os",
}

# "Standard library only" as an explicit allowlist: a new import is a conscious decision.
ALLOWED_IMPORTS = {
    "__future__",
    "argparse",
    "calmoji",
    "contextlib",
    "gzip",
    "hashlib",
    "io",
    "pathlib",
    "re",
    "shutil",
    "stat",
    "sys",
    "tarfile",
    "typing",
    "zipfile",
}


def _imported_top_level_modules() -> set:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"), filename=str(SCRIPT))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    return imported


def test_script_uses_no_clock_host_user_or_randomness():
    assert not _imported_top_level_modules() & NONDETERMINISTIC_MODULES


def test_script_imports_only_the_standard_library_and_calmoji():
    assert _imported_top_level_modules() <= ALLOWED_IMPORTS


# -----------------------------------------------------------------------------
# Size budget
# -----------------------------------------------------------------------------


def test_every_file_in_the_bundle_is_within_budget_and_the_largest_is_reported(built):
    result, _ = built
    stats = bb.measure_files(result.bundle_dir)
    assert len(stats) == result.ics_count
    assert all(f.events <= MAX_EVENTS_PER_FILE and f.size <= MAX_BYTES_PER_FILE for f in stats)

    assert result.largest_by_events.events == max(f.events for f in stats)
    assert result.largest_by_size.size == max(f.size for f in stats)
    assert result.largest_by_size.size == (result.bundle_dir / result.largest_by_size.path).stat().st_size
    # counted the way a calendar app would: BEGIN:VEVENT lines
    text = (result.bundle_dir / result.largest_by_events.path).read_text(encoding="utf-8")
    assert text.count("BEGIN:VEVENT") == result.largest_by_events.events


def test_check_budget_names_every_offender():
    fine = bb.FileStats("a.ics", MAX_EVENTS_PER_FILE, MAX_BYTES_PER_FILE)
    too_many = bb.FileStats("b.ics", MAX_EVENTS_PER_FILE + 1, 1000)
    too_big = bb.FileStats("c.ics", 10, MAX_BYTES_PER_FILE + 1)

    bb.check_budget([fine])
    with pytest.raises(bb.BundleBudgetError) as excinfo:
        bb.check_budget([fine, too_many, too_big])
    message = str(excinfo.value)
    assert "b.ics" in message and "c.ics" in message and "a.ics" not in message


@needs_install
def test_the_build_fails_if_any_file_is_over_budget(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(bb, "MAX_EVENTS_PER_FILE", 100)  # the generator itself still allows 600

    assert bb.main(["--out", str(tmp_path), "--years", "2027", "--alignments", "academic"]) == 1
    err = capsys.readouterr().err
    assert "over the budget" in err
    assert not list(tmp_path.glob("*.zip")) and not list(tmp_path.glob("*.tar.gz"))


@needs_install
def test_a_file_the_writer_refuses_also_fails_the_build_cleanly(tmp_path, monkeypatch, capsys):
    def refuse(argv):
        raise IcsBudgetError("somewhere.ics: 601 events is over the budget of 600 per file.")

    monkeypatch.setattr(bb, "calmoji_main", refuse)

    assert bb.main(["--out", str(tmp_path), "--years", "2027", "--alignments", "academic"]) == 1
    assert "error: somewhere.ics" in capsys.readouterr().err


@needs_install
def test_main_reports_the_budget_and_the_largest_files(tmp_path, capsys):
    assert bb.main(["--out", str(tmp_path), "--years", "2027", "--alignments", "academic"]) == 0
    shown = capsys.readouterr().out

    assert f"Budget per file: {MAX_EVENTS_PER_FILE} events and {MAX_BYTES_PER_FILE:,} bytes" in shown
    assert re.search(r"^Largest file by events: \d+ events, [\d,]+ bytes \(.+\.ics\)$", shown, re.M)
    assert re.search(r"^Largest file by size: \d+ events, [\d,]+ bytes \(.+\.ics\)$", shown, re.M)
