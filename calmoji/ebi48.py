# calmoji/ebi48.py

from __future__ import annotations

import datetime
from typing import Mapping


"""
EBI48_CLOCK — The Canonical Emoji Time Table

Maps 48 half-hour slots to unique, symbolic glyphs.

Design:
- UTC day is split into 48 half-hour slots.
- Slot boundaries are anchored at :05 and :35 past each hour.
  - slot (hour*2)     starts at HH:05 UTC
  - slot (hour*2 + 1) starts at HH:35 UTC

This matches Calmoji meeting cadence (25 minutes + decompression buffer) cleanly.
"""

EBI48_CLOCK: Mapping[int, tuple[str, str]] = {
    0:  ("🐶", "Dog Face"),
    1:  ("🦨", "Skunk Face"),
    2:  ("🐱", "Cat Face"),
    3:  ("🐦", "Bird Face"),
    4:  ("🐭", "Mouse Face"),
    5:  ("🦬", "Bison Face"),
    6:  ("🦝", "Raccoon Face"),
    7:  ("🦚", "Peacock Face"),
    8:  ("🐰", "Bunny Face"),
    9:  ("🦦", "Otter Face"),
    10: ("🦊", "Fox Face"),
    11: ("🦫", "Beaver Face"),
    12: ("🐻", "Bear Face"),
    13: ("🦙", "Llama Face"),
    14: ("🐴", "Horse Face"),
    15: ("🦌", "Deer Face"),
    16: ("🐐", "Goat Face"),
    17: ("🦥", "Sloth Face"),
    18: ("🐯", "Tiger Face"),
    19: ("🐘", "Elephant Face"),
    20: ("🦁", "Lion Face"),
    21: ("🌙", "Crescent Face"),
    22: ("💠", "Diamond Face"),
    23: ("🦢", "Swan Face"),
    24: ("🐸", "Frog Face"),
    25: ("🦎", "Lizard Face"),
    26: ("🪱", "Worm Face"),
    27: ("🕊️", "Dove Face"),
    28: ("🐔", "Chicken Face"),
    29: ("🌲", "Tree Face"),
    30: ("🦔", "Hedgehog Face"),
    31: ("🪿", "Goose Face"),
    32: ("🦡", "Badger Face"),
    33: ("🦃", "Turkey Face"),
    34: ("🦜", "Parrot Face"),
    35: ("🦉", "Owl Face"),
    36: ("🐺", "Wolf Face"),
    37: ("🦇", "Bat Face"),
    38: ("🦆", "Duck Face"),
    39: ("🪺", "Nest Face"),
    40: ("⛰️", "Mountain Face"),
    41: ("🐢", "Turtle Face"),
    42: ("🦭", "Seal Face"),
    43: ("🐞", "Ladybug Face"),
    44: ("🦑", "Squid Face"),
    45: ("🐙", "Octopus Face"),
    46: ("🐠", "Fish Face"),
    47: ("🦈", "Shark Face"),
}


def get_slot_index_for_time(dt: datetime.datetime) -> int:
    """
    Return the canonical EBI48 slot index for a UTC datetime.

    Valid start minutes for slot anchors are strictly:
    - HH:05 -> even slot (hour*2)
    - HH:35 -> odd slot  (hour*2 + 1)

    Raises:
        ValueError if dt is not anchored to :05 or :35.
    """
    hour = dt.hour
    minute = dt.minute

    if minute == 5:
        return hour * 2
    if minute == 35:
        return hour * 2 + 1

    raise ValueError(
        f"Invalid start minute for EBI48 mapping: {dt.isoformat()} "
        "(expected minute == 5 or 35)"
    )


def get_emoji_for_slot(slot: int) -> tuple[str, str]:
    """Return (emoji, face name) for a given 0–47 slot index."""
    if slot < 0 or slot > 47:
        return ("❓", "Unknown Face")
    return EBI48_CLOCK.get(slot, ("❓", "Unknown Face"))


def get_emoji_name_for_slot(slot: int) -> str:
    """Return only the face name for a given slot index."""
    return get_emoji_for_slot(slot)[1]


def get_emoji_for_time(dt: datetime.datetime) -> tuple[str, str]:
    """
    Map a UTC datetime (anchored to :05 or :35) to its EBI48 emoji + name.
    """
    slot = get_slot_index_for_time(dt)
    return get_emoji_for_slot(slot)


def get_slot_index_for_emoji(emoji: str) -> int:
    """Reverse lookup: emoji -> slot index."""
    for idx, (e, _) in EBI48_CLOCK.items():
        if e == emoji:
            return idx
    raise ValueError(f"Emoji {emoji!r} not found in EBI48 clock.")


def get_all_ebi48_slots() -> list[tuple[int, str, str]]:
    """Return (slot_index, emoji, label) for all 48 slots."""
    return [(i, emoji, label) for i, (emoji, label) in EBI48_CLOCK.items()]