# tests/test_version.py
"""--version: installed metadata first, then pyproject.toml in a source checkout, then 0.0.0+local."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import calmoji

ROOT = Path(__file__).resolve().parent.parent

PYPROJECT = """\
[build-system]
requires = ["setuptools>=68"]

[project]
name = "calmoji"
version = "{version}"  # bumped by hand
description = "x"

[tool.black]
target-version = ["py39"]
"""


def write_pyproject(path: Path, version: str = "1.2.3", text: str = "") -> Path:
    path.write_text(text or PYPROJECT.format(version=version), encoding="utf-8")
    return path


# -----------------------------------------------------------------------------
# Reading pyproject.toml
# -----------------------------------------------------------------------------


def test_pyproject_version_is_read_from_the_version_line(tmp_path):
    assert calmoji._pyproject_version(write_pyproject(tmp_path / "pyproject.toml", "1.2.3")) == "1.2.3"


def test_the_version_line_may_carry_a_comment_and_pre_release_tags(tmp_path):
    assert calmoji._pyproject_version(write_pyproject(tmp_path / "p.toml", "0.2.0rc1")) == "0.2.0rc1"


def test_target_version_lines_are_not_mistaken_for_the_version(tmp_path):
    text = '[project]\nname = "calmoji"\n\n[tool.black]\ntarget-version = ["py39"]\nversion = "7.7.7"\n'
    # the first line that is exactly `version = "..."` wins; target-version never matches
    assert calmoji._pyproject_version(write_pyproject(tmp_path / "p.toml", text=text)) == "7.7.7"


@pytest.mark.parametrize(
    "text",
    [
        '[project]\nname = "calmoji"\ndescription = "no version here"\n',
        '[project]\nname = "calmoji"\nversion = 1.2.3\n',  # not a string
        "[project]\nname = 'calmoji'\nversion = '1.2.3'\n",  # single-quoted TOML: not matched, by design
        '[project]\nname = "someone-elses-project"\nversion = "4.5.6"\n',  # not calmoji's file
        "",
    ],
)
def test_a_pyproject_without_a_usable_version_gives_none(tmp_path, text):
    assert calmoji._pyproject_version(write_pyproject(tmp_path / "p.toml", text=text or "\n")) is None


def test_a_missing_or_unreadable_pyproject_gives_none(tmp_path):
    assert calmoji._pyproject_version(tmp_path / "missing.toml") is None
    assert calmoji._pyproject_version(tmp_path) is None  # a directory: reading it raises OSError
    binary = tmp_path / "binary.toml"
    binary.write_bytes(b"\xff\xfe\x00 not utf-8 \xc3\x28")
    assert calmoji._pyproject_version(binary) is None


def test_the_real_pyproject_is_readable():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    expected = re.search(r'^version = "([^"]+)"', text, re.M)
    assert expected is not None
    assert calmoji._pyproject_version(ROOT / "pyproject.toml") == expected.group(1)


# -----------------------------------------------------------------------------
# Resolution order
# -----------------------------------------------------------------------------


def test_installed_metadata_wins(monkeypatch, tmp_path):
    monkeypatch.setattr(calmoji, "_metadata_version", lambda: "9.9.9")
    monkeypatch.setattr(calmoji, "_PYPROJECT", write_pyproject(tmp_path / "pyproject.toml", "1.2.3"))
    assert calmoji._resolve_version() == "9.9.9"


def test_without_metadata_it_falls_back_to_pyproject(monkeypatch, tmp_path):
    monkeypatch.setattr(calmoji, "_metadata_version", lambda: None)
    monkeypatch.setattr(calmoji, "_PYPROJECT", write_pyproject(tmp_path / "pyproject.toml", "1.2.3"))
    assert calmoji._resolve_version() == "1.2.3"


def test_without_metadata_or_pyproject_it_is_the_local_marker(monkeypatch, tmp_path):
    monkeypatch.setattr(calmoji, "_metadata_version", lambda: None)
    monkeypatch.setattr(calmoji, "_PYPROJECT", tmp_path / "does-not-exist.toml")
    assert calmoji._resolve_version() == "0.0.0+local"


def test_an_unreadable_pyproject_also_gives_the_local_marker(monkeypatch, tmp_path):
    monkeypatch.setattr(calmoji, "_metadata_version", lambda: None)
    monkeypatch.setattr(calmoji, "_PYPROJECT", tmp_path)  # a directory
    assert calmoji._resolve_version() == "0.0.0+local"


def test_the_version_is_a_string_and_never_empty():
    assert isinstance(calmoji.__version__, str) and calmoji.__version__


# -----------------------------------------------------------------------------
# The real thing: python3 calmoji.py --version from an uninstalled clone
# -----------------------------------------------------------------------------


@pytest.fixture
def checkout(tmp_path) -> Path:
    """A copy of the source tree with no egg-info, as a fresh clone has."""
    clone = tmp_path / "clone"
    clone.mkdir()
    shutil.copytree(ROOT / "calmoji", clone / "calmoji", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(ROOT / "calmoji.py", clone / "calmoji.py")
    shutil.copy(ROOT / "pyproject.toml", clone / "pyproject.toml")
    return clone


def version_output(clone: Path) -> str:
    # -S: no site-packages, so no installed calmoji can answer. Python-specific env vars are dropped.
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    done = subprocess.run(
        [sys.executable, "-S", "calmoji.py", "--version"], cwd=clone, env=env, capture_output=True, text=True
    )
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def test_version_from_a_source_checkout_reads_pyproject(checkout):
    expected = calmoji._pyproject_version(ROOT / "pyproject.toml")
    assert version_output(checkout) == f"calmoji {expected}"
    assert "0.0.0+local" not in version_output(checkout)


def test_version_follows_the_checkouts_own_pyproject(checkout):
    write_pyproject(checkout / "pyproject.toml", "9.8.7")
    assert version_output(checkout) == "calmoji 9.8.7"


def test_version_is_local_only_when_pyproject_cannot_be_found(checkout):
    (checkout / "pyproject.toml").unlink()
    assert version_output(checkout) == "calmoji 0.0.0+local"
