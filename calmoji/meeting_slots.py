# calmoji/meeting_slots.py

"""
🕒 calmoji meeting slots — fixed in UTC, all year.

Slots never move: a city's slot has the same UTC time (and so the same EBI48
emoji) in January and in July. Calendar apps already show UTC events in each
viewer's local time, daylight saving time included, so calmoji carries no
time-zone or DST logic. Where a city observes daylight saving time, the local
time of its slot is an hour earlier in winter than in summer, and the slot's
description says so (see CITY_ZONES and describe_slot).

Every slot starts at :05 or :35 UTC: the EBI48 emoji tag depends on it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class CityZone:
    """
    What a city's slot descriptions say about local time. Static text only:
    offsets are in minutes east of UTC, and nothing here looks at a date.
    """

    std_offset_minutes: int
    std_abbr: str
    dst_offset_minutes: Optional[int] = None  # summer time, if the city has it
    dst_abbr: Optional[str] = None
    southern: bool = False  # "summer" is the southern summer (December to February)
    period: str = "Early afternoon"


CITY_ZONES: Dict[str, CityZone] = {
    "Auckland": CityZone(720, "NZST", 780, "NZDT", southern=True, period="Afternoon"),
    "Tokyo": CityZone(540, "JST"),
    "Delhi": CityZone(330, "IST"),
    "Mecca": CityZone(180, "AST"),
    "Brussels": CityZone(60, "CET", 120, "CEST"),
    "Havana": CityZone(-300, "CST", -240, "CDT"),
    "Seattle": CityZone(-480, "PST", -420, "PDT"),
}

# (City, start hour, start minute, end hour, end minute), all UTC.
MEETING_SLOTS: List[Tuple[str, int, int, int, int]] = [
    ("Auckland", 2, 35, 3, 0),  # Slot A: 15:35 NZDT / 14:35 NZST
    ("Auckland", 3, 5, 3, 30),  # Slot B
    ("Tokyo", 4, 35, 5, 0),  # Slot A: 13:35 JST
    ("Tokyo", 5, 5, 5, 30),  # Slot B
    ("Delhi", 8, 5, 8, 30),  # Slot A: 13:35 IST
    ("Delhi", 8, 35, 9, 0),  # Slot B
    ("Mecca", 10, 35, 11, 0),  # Slot A: 13:35 AST
    ("Mecca", 11, 5, 11, 30),  # Slot B
    ("Brussels", 11, 35, 12, 0),  # Slot A: 13:35 CEST / 12:35 CET
    ("Brussels", 12, 5, 12, 30),  # Slot B
    ("Havana", 17, 35, 18, 0),  # Slot A: 13:35 CDT / 12:35 CST
    ("Havana", 18, 5, 18, 30),  # Slot B
    ("Seattle", 20, 35, 21, 0),  # Slot A: 13:35 PDT / 12:35 PST
    ("Seattle", 21, 5, 21, 30),  # Slot B
]


def _clock(minutes: int) -> str:
    minutes %= 24 * 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _local_range(start_hour: int, start_minute: int, end_hour: int, end_minute: int, offset_minutes: int) -> str:
    start = start_hour * 60 + start_minute + offset_minutes
    end = end_hour * 60 + end_minute + offset_minutes
    return f"{_clock(start)}–{_clock(end)}"


def describe_slot(city: str, start_hour: int, start_minute: int, end_hour: int, end_minute: int) -> str:
    """
    Say, in words that are true all year, when a slot falls in the city's local time.

    Example: "Early afternoon in Brussels: 13:35–14:00 CEST in summer and
    12:35–13:00 CET in winter. Fixed at 11:35 UTC."

    No commas or semicolons: RFC 5545 requires them to be escaped in TEXT values.
    """
    zone = CITY_ZONES[city]
    fixed = f"Fixed at {_clock(start_hour * 60 + start_minute)} UTC."

    std = _local_range(start_hour, start_minute, end_hour, end_minute, zone.std_offset_minutes)
    if zone.dst_offset_minutes is None or zone.dst_abbr is None:
        return f"{zone.period} in {city}: {std} {zone.std_abbr}. {fixed}"

    summer = _local_range(start_hour, start_minute, end_hour, end_minute, zone.dst_offset_minutes)
    in_summer, in_winter = (
        ("in the southern summer", "in the southern winter") if zone.southern else ("in summer", "in winter")
    )
    return (
        f"{zone.period} in {city}: {summer} {zone.dst_abbr} {in_summer} and {std} {zone.std_abbr} {in_winter}. {fixed}"
    )
