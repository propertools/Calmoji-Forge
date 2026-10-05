# calmoji/filenames.py

"""
The names of the files calmoji writes, defined once.

Every writer builds its names with the functions here, and calmoji/output_dir.py
decides what it may delete with the patterns here, each defined right under its
builder. So the code that writes a name and the code that recognises it as calmoji's
own can't drift apart (tests check that every name a run produces matches a pattern).

A file is calmoji's only if its name matches exactly. Any year is fine
(re-running for 2028 cleans 2027's files), but "family.ics" is not calmoji's.
"""

from __future__ import annotations

import re
from typing import Pattern

YEAR = r"[0-9]{4}"
MONTH = r"(?:0[1-9]|1[0-2])"

# The two subfolders of an output folder, and the prefix of the monthly files inside each
# (focus/focus_2027-09.ics, meetings/meetings_2027-09.ics).
FOCUS_DIR = "focus"
MEETINGS_DIR = "meetings"
FOCUS_PREFIX = "focus"
MEETINGS_PREFIX = "meetings"


def seasons_filename(year: int | str) -> str:
    return f"seasons_{year}.ics"


SEASONS_FILE: Pattern[str] = re.compile(rf"seasons_{YEAR}\.ics")


def emoji_clock_filename(year: int) -> str:
    return f"emoji_clock_{year}.ics"


EMOJI_CLOCK_FILE: Pattern[str] = re.compile(rf"emoji_clock_{YEAR}\.ics")


def monthly_filename(prefix: str, month: str) -> str:
    """<prefix>_<YYYY-MM>.ics, for example focus_2027-09.ics."""
    return f"{prefix}_{month}.ics"


FOCUS_FILE: Pattern[str] = re.compile(rf"{FOCUS_PREFIX}_{YEAR}-{MONTH}\.ics")
MEETINGS_FILE: Pattern[str] = re.compile(rf"{MEETINGS_PREFIX}_{YEAR}-{MONTH}\.ics")

# What may sit directly in an output folder, and in each of its two subfolders.
TOP_LEVEL_FILES = (SEASONS_FILE, EMOJI_CLOCK_FILE)
SUBFOLDER_FILES = {FOCUS_DIR: FOCUS_FILE, MEETINGS_DIR: MEETINGS_FILE}


def is_top_level_calmoji_file(name: str) -> bool:
    return any(pattern.fullmatch(name) for pattern in TOP_LEVEL_FILES)


def is_subfolder_calmoji_file(folder: str, name: str) -> bool:
    return SUBFOLDER_FILES[folder].fullmatch(name) is not None
