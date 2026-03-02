# tests/test_meeting_slots.py

import datetime
import unicodedata
from collections import defaultdict

from calmoji.calendar_config import DEFAULT_ALIGNMENT
from calmoji.calendar_phases import get_semester_phases
from calmoji.slot_generator import generate_meeting_slots, is_valid_slot_day
from calmoji.ebi48 import get_emoji_for_time
from calmoji.meeting_slots import MEETING_SLOTS

UTC = datetime.timezone.utc


def to_datetime(hour: int, minute: int) -> datetime.datetime:
    """UTC-aware datetime on a fixed reference day."""
    return datetime.datetime(2025, 1, 1, hour, minute, tzinfo=UTC)


# -----------------------------------------------------------------------------
# Slot config validation
# -----------------------------------------------------------------------------

def test_all_slot_labels_are_present():
    for slot in MEETING_SLOTS:
        label = slot[-1]
        assert isinstance(label, str)
        assert (":" in label) or ("–" in label), f"Slot label missing delimiter: {label}"


def test_utc_hour_ranges_are_valid():
    for _, sh, sm, eh, em, _ in MEETING_SLOTS:
        assert 0 <= sh < 24
        assert 0 <= eh < 24
        assert 0 <= sm < 60
        assert 0 <= em < 60


def test_meeting_slots_duration_and_alignment():
    region_slots = defaultdict(list)

    for region, sh, sm, eh, em, label in MEETING_SLOTS:
        start = to_datetime(sh, sm)
        end = to_datetime(eh, em)
        duration = end - start

        assert duration == datetime.timedelta(minutes=25), f"{region} {label} is not 25 minutes long"
        assert sm in (5, 35), f"{region} {label} does not start at :05 or :35"

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
        if ch in ("\uFE0F", "\u200D"):
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
        "circle", "square", "diamond", "star", "moon", "sun", "globe", "symbol", "sparkle",
        "black", "white", "large", "small",
    }
    for evt in get_mecca_events():
        emoji_char = evt.summary.split(" ")[1]
        assert emoji_char != "❓", f"Mecca slot maps to unknown emoji: {evt.summary}"
        name_blob = _unicode_name_lower(emoji_char)
        assert any(kw in name_blob for kw in safe_keywords), (
            f"Mecca slot emoji does not look 'symbolic/geometric' by name: {emoji_char!r} ({name_blob})"
        )
