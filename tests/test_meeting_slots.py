# tests/test_meeting_slots.py

import datetime
import re
import unicodedata
from collections import defaultdict

import pytest

from calmoji.calendar_config import DEFAULT_ALIGNMENT
from calmoji.calendar_phases import get_semester_phases
from calmoji.ebi48 import get_emoji_for_time
from calmoji.meeting_slots import CITY_ZONES, MEETING_SLOTS, describe_slot
from calmoji.slot_generator import generate_meeting_slots, is_valid_slot_day

UTC = datetime.timezone.utc


def to_datetime(hour: int, minute: int) -> datetime.datetime:
    """UTC-aware datetime on a fixed reference day."""
    return datetime.datetime(2025, 1, 1, hour, minute, tzinfo=UTC)


# -----------------------------------------------------------------------------
# Slot config validation
# -----------------------------------------------------------------------------


def test_every_slot_city_has_a_zone_table_entry():
    assert {slot[0] for slot in MEETING_SLOTS} == set(CITY_ZONES)


def test_utc_hour_ranges_are_valid():
    for _, sh, sm, eh, em in MEETING_SLOTS:
        assert 0 <= sh < 24
        assert 0 <= eh < 24
        assert 0 <= sm < 60
        assert 0 <= em < 60


def test_meeting_slots_duration_and_alignment():
    region_slots = defaultdict(list)

    for region, sh, sm, eh, em in MEETING_SLOTS:
        start = to_datetime(sh, sm)
        end = to_datetime(eh, em)
        duration = end - start

        assert duration == datetime.timedelta(minutes=25), f"{region} {sh}:{sm} is not 25 minutes long"
        assert sm in (5, 35), f"{region} {sh}:{sm} does not start at :05 or :35"

        region_slots[region].append((start, end))

    # Ensure no overlapping slots within regions
    for region, slots in region_slots.items():
        slots.sort()
        for i in range(1, len(slots)):
            assert slots[i][0] >= slots[i - 1][1], f"Overlap detected in {region} between slots {i-1} and {i}"


def test_emoji_assignment_for_all_slots():
    seen_emojis = set()

    for region, sh, sm, *_ in MEETING_SLOTS:
        emoji_char, face_name = get_emoji_for_time(to_datetime(sh, sm))
        assert emoji_char and emoji_char.strip(), f"Empty emoji for {region} {face_name}"
        assert emoji_char != "❓", f"Unknown emoji mapping for {region} {face_name}"

        # Uniqueness check is nice, but if you ever intentionally reuse glyphs,
        # this will be the one to relax.
        assert emoji_char not in seen_emojis, f"Duplicate emoji {emoji_char} in {region} {face_name}"
        seen_emojis.add(emoji_char)


def test_all_meeting_slots_map_to_valid_emoji():
    for city, sh, sm, *_ in MEETING_SLOTS:
        dt = to_datetime(sh, sm)
        emoji_char, label = get_emoji_for_time(dt)
        assert emoji_char != "❓", f"{city} at {sh:02}:{sm:02} maps to unknown emoji!"
        assert label != "Unknown Face", f"{city} at {sh:02}:{sm:02} maps to unknown label!"


# -----------------------------------------------------------------------------
# Mecca behavior tests (new API)
# -----------------------------------------------------------------------------


def _get_first_meeting_phase(year: int = 2025, alignment: str = DEFAULT_ALIGNMENT):
    phases = get_semester_phases(year, alignment)
    # first phase should allow meetings in your current heuristic model
    return phases[0]


def get_mecca_events(year: int = 2025, alignment: str = DEFAULT_ALIGNMENT):
    phase = _get_first_meeting_phase(year, alignment)
    events = generate_meeting_slots(phase, include_oceania=False)
    return [e for e in events if e.summary.startswith("Mecca ")]


def _unicode_name_lower(s: str) -> str:
    """
    Best-effort unicode name lookup for an emoji string.
    For multi-codepoint emoji, we check all codepoints that have names.
    """
    names = []
    for ch in s:
        # skip variation selectors / joiners
        if ch in ("\ufe0f", "\u200d"):
            continue
        try:
            names.append(unicodedata.name(ch).lower())
        except ValueError:
            pass
    return " ".join(names)


def test_mecca_weekdays_are_sunday_to_thursday():
    # (weekday: 0=Mon ... 6=Sun)
    allowed = {6, 0, 1, 2, 3}
    for evt in get_mecca_events():
        weekday = evt.start.weekday()
        assert weekday in allowed, f"Invalid Mecca slot on weekday {weekday} for {evt.start.isoformat()}"


def test_mecca_slot_durations_are_25_minutes():
    for evt in get_mecca_events():
        assert evt.end is not None
        duration = evt.end - evt.start
        assert duration == datetime.timedelta(minutes=25), f"Mecca {evt.summary} is not 25 minutes long"


def test_mecca_slots_have_valid_emoji_faces():
    for evt in get_mecca_events():
        # Current summary format: "Mecca {emoji} {face_name} Slot (...)"
        assert " Face" in evt.summary, f"Missing emoji face label in: {evt.summary}"


def test_mecca_slots_use_city_weekday_policy():
    # This test anchors on the actual helper used by slot generation
    for evt in get_mecca_events():
        assert is_valid_slot_day("Mecca", evt.start.weekday()), f"Mecca event violates weekday policy: {evt.start}"


def test_mecca_slots_use_geometric_or_symbolic_emoji_names():
    """
    Replace the old emoji-library-based allowlist with a stdlib heuristic:
    ensure the emoji's unicode name contains at least one "safe" keyword.
    """
    safe_keywords = {
        "circle",
        "square",
        "diamond",
        "star",
        "moon",
        "sun",
        "globe",
        "symbol",
        "sparkle",
        "black",
        "white",
        "large",
        "small",
    }
    for evt in get_mecca_events():
        emoji_char = evt.summary.split(" ")[1]
        assert emoji_char != "❓", f"Mecca slot maps to unknown emoji: {evt.summary}"
        name_blob = _unicode_name_lower(emoji_char)
        assert any(
            kw in name_blob for kw in safe_keywords
        ), f"Mecca slot emoji does not look 'symbolic/geometric' by name: {emoji_char!r} ({name_blob})"


# -----------------------------------------------------------------------------
# Fixed in UTC, labelled honestly
# -----------------------------------------------------------------------------

# Written out by hand, independently of the zone table in calmoji/meeting_slots.py.
EXPECTED_DESCRIPTIONS = {
    (
        "Auckland",
        "02:35",
    ): "Afternoon in Auckland: 15:35–16:00 NZDT in the southern summer and 14:35–15:00 NZST in the southern winter. Fixed at 02:35 UTC.",
    (
        "Auckland",
        "03:05",
    ): "Afternoon in Auckland: 16:05–16:30 NZDT in the southern summer and 15:05–15:30 NZST in the southern winter. Fixed at 03:05 UTC.",
    ("Tokyo", "04:35"): "Early afternoon in Tokyo: 13:35–14:00 JST. Fixed at 04:35 UTC.",
    ("Tokyo", "05:05"): "Early afternoon in Tokyo: 14:05–14:30 JST. Fixed at 05:05 UTC.",
    ("Delhi", "08:05"): "Early afternoon in Delhi: 13:35–14:00 IST. Fixed at 08:05 UTC.",
    ("Delhi", "08:35"): "Early afternoon in Delhi: 14:05–14:30 IST. Fixed at 08:35 UTC.",
    ("Mecca", "10:35"): "Early afternoon in Mecca: 13:35–14:00 AST. Fixed at 10:35 UTC.",
    ("Mecca", "11:05"): "Early afternoon in Mecca: 14:05–14:30 AST. Fixed at 11:05 UTC.",
    (
        "Brussels",
        "11:35",
    ): "Early afternoon in Brussels: 13:35–14:00 CEST in summer and 12:35–13:00 CET in winter. Fixed at 11:35 UTC.",
    (
        "Brussels",
        "12:05",
    ): "Early afternoon in Brussels: 14:05–14:30 CEST in summer and 13:05–13:30 CET in winter. Fixed at 12:05 UTC.",
    (
        "Havana",
        "17:35",
    ): "Early afternoon in Havana: 13:35–14:00 CDT in summer and 12:35–13:00 CST in winter. Fixed at 17:35 UTC.",
    (
        "Havana",
        "18:05",
    ): "Early afternoon in Havana: 14:05–14:30 CDT in summer and 13:05–13:30 CST in winter. Fixed at 18:05 UTC.",
    (
        "Seattle",
        "20:35",
    ): "Early afternoon in Seattle: 13:35–14:00 PDT in summer and 12:35–13:00 PST in winter. Fixed at 20:35 UTC.",
    (
        "Seattle",
        "21:05",
    ): "Early afternoon in Seattle: 14:05–14:30 PDT in summer and 13:05–13:30 PST in winter. Fixed at 21:05 UTC.",
}

# City -> (standard offset, summer offset or None) in hours east of UTC, from the usual references.
EXPECTED_OFFSETS = {
    "Auckland": (12, 13),
    "Tokyo": (9, None),
    "Delhi": (5.5, None),
    "Mecca": (3, None),
    "Brussels": (1, 2),
    "Havana": (-5, -4),
    "Seattle": (-8, -7),
}
EXPECTED_ABBREVIATIONS = {
    "Auckland": ("NZST", "NZDT"),
    "Tokyo": ("JST", None),
    "Delhi": ("IST", None),
    "Mecca": ("AST", None),
    "Brussels": ("CET", "CEST"),
    "Havana": ("CST", "CDT"),
    "Seattle": ("PST", "PDT"),
}

DESCRIPTION_RE = re.compile(r"Fixed at (\d\d):(\d\d) UTC\.$")
CLOCK_RE = re.compile(r"\d{1,2}:\d{2}")


def all_slot_events(year: int, alignment: str):
    events = []
    for phase in get_semester_phases(year, alignment):
        events.extend(generate_meeting_slots(phase, include_oceania=True))
    return events


def first_line(event) -> str:
    return event.description.split("\n")[0]


def test_zone_table_matches_the_independent_offsets():
    assert set(CITY_ZONES) == set(EXPECTED_OFFSETS)
    for city, zone in CITY_ZONES.items():
        std, summer = EXPECTED_OFFSETS[city]
        assert zone.std_offset_minutes == std * 60, city
        assert zone.dst_offset_minutes == (None if summer is None else summer * 60), city
        assert (zone.std_abbr, zone.dst_abbr) == EXPECTED_ABBREVIATIONS[city], city


def test_descriptions_are_exactly_the_expected_text():
    texts = {}
    for city, sh, sm, eh, em in MEETING_SLOTS:
        texts[(city, f"{sh:02d}:{sm:02d}")] = describe_slot(city, sh, sm, eh, em)
    assert texts == EXPECTED_DESCRIPTIONS


def test_fixed_at_time_equals_the_slots_real_utc_start():
    events = all_slot_events(2027, "academic")
    assert events
    for event in events:
        match = DESCRIPTION_RE.search(first_line(event))
        assert match, event.description
        assert (int(match.group(1)), int(match.group(2))) == (event.start.hour, event.start.minute), event.summary


def test_local_times_in_descriptions_follow_from_the_offset_table():
    # Summer (or, with no summer time, standard) local time of slot A is the 13:35 / 14:05 pattern;
    # Auckland's southern summer is 15:35 / 16:05.
    for city, sh, sm, *_ in MEETING_SLOTS:
        std, summer = EXPECTED_OFFSETS[city]
        offset = std if summer is None else summer
        local_start = (sh * 60 + sm + int(offset * 60)) % 1440
        expected = {"Auckland": {15 * 60 + 35, 16 * 60 + 5}}.get(city, {13 * 60 + 35, 14 * 60 + 5})
        assert local_start in expected, f"{city} {sh}:{sm} is {local_start // 60}:{local_start % 60:02d} local"
        if summer is not None:
            winter = (sh * 60 + sm + int(std * 60)) % 1440
            assert winter == local_start - 60


def test_titles_carry_no_local_time_and_no_time_zone_abbreviation():
    abbreviations = {a for pair in EXPECTED_ABBREVIATIONS.values() for a in pair if a}
    events = all_slot_events(2027, "academic") + all_slot_events(2028, "calendar")
    assert events
    for event in events:
        assert not CLOCK_RE.search(event.summary), event.summary
        assert "UTC" not in event.summary, event.summary
        assert "(" not in event.summary and ")" not in event.summary, event.summary
        assert not abbreviations & set(re.findall(r"[A-Za-z]+", event.summary)), event.summary


def test_title_format():
    swan = [e for e in all_slot_events(2027, "calendar") if e.summary.startswith("Brussels ") and e.start.minute == 35]
    assert swan and all(e.summary == "Brussels 🦢 Swan Face Slot" for e in swan)


def test_delhi_and_auckland_slot_a_times():
    delhi = [e for e in all_slot_events(2027, "academic") if e.summary.startswith("Delhi ")]
    auckland = [e for e in all_slot_events(2027, "academic") if e.summary.startswith("Auckland ")]
    assert (delhi[0].start.hour, delhi[0].start.minute) == (8, 5)
    assert (delhi[1].start.hour, delhi[1].start.minute) == (8, 35)
    assert (auckland[0].start.hour, auckland[0].start.minute) == (2, 35)
    assert (auckland[1].start.hour, auckland[1].start.minute) == (3, 5)


def test_auckland_is_only_emitted_when_asked_for():
    phase = get_semester_phases(2027, "academic")[0]
    assert not any(e.summary.startswith("Auckland") for e in generate_meeting_slots(phase))
    assert any(e.summary.startswith("Auckland") for e in generate_meeting_slots(phase, include_oceania=True))


@pytest.mark.parametrize("alignment", ["academic", "calendar"])
def test_every_slot_starts_at_5_or_35_past_and_never_moves_in_utc(alignment):
    events = all_slot_events(2028, alignment)  # a leap year, whatever the alignment
    assert events

    seen = {}
    for event in events:
        assert event.start.minute in (5, 35), event.summary
        city_slot = (event.summary.split(" ")[0], event.start.hour, event.start.minute)
        seen.setdefault(city_slot, set()).add(event.summary)  # includes the EBI48 emoji
    # one summary (hence one emoji) per city slot, all year
    assert all(len(summaries) == 1 for summaries in seen.values())
    # and exactly the configured slots
    assert set(seen) == {(c, sh, sm) for c, sh, sm, _, _ in MEETING_SLOTS}


@pytest.mark.parametrize("alignment", ["academic", "calendar"])
def test_a_slot_has_the_same_utc_time_and_emoji_in_january_and_july(alignment):
    events = all_slot_events(2028, alignment)
    january = {(e.summary, e.start.hour, e.start.minute) for e in events if e.start.month == 1}
    july = {(e.summary, e.start.hour, e.start.minute) for e in events if e.start.month == 7}
    assert january and july
    assert january == july


def test_meeting_slot_weekday_rules_are_unchanged():
    for event in all_slot_events(2027, "academic"):
        weekday = event.start.weekday()
        if event.summary.startswith("Mecca "):
            assert weekday in {6, 0, 1, 2, 3}
        else:
            assert weekday in {0, 1, 2, 3, 4}
