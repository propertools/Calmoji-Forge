# tests/test_emoji_clock.py

from calmoji.ebi48 import EBI48_CLOCK
from datetime import datetime

def test_ebi48_unique_emojis():
    emojis = [emoji for emoji, _ in EBI48_CLOCK.values()]
    assert len(set(emojis)) == 48, "All EBI48 emojis must be unique"

def test_ebi48_all_labels_are_strings():
    for emoji, label in EBI48_CLOCK.values():
        assert isinstance(label, str)
        assert len(label) > 3

def validate_ebi48_clock():
    assert len(EBI48_CLOCK) == 48, "EBI48_CLOCK must have exactly 48 slots"
    emoji_set = set()
    # Yes, this test overlaps test_ebi48_unique_emojis(), this is a feature and not a bug!
    for k, (emoji, name) in EBI48_CLOCK.items():
        assert emoji not in emoji_set, f"Duplicate emoji: {emoji} at slot {k}"
        emoji_set.add(emoji)

def test_ebi48_clock_completeness():
    assert len(EBI48_CLOCK) == 48, "There should be exactly 48 unique emoji slots"

def test_ebi48_clock_uniqueness():
    emojis = [e for e, _ in EBI48_CLOCK.values()]
    assert len(set(emojis)) == 48, "All emojis must be unique"

def test_ebi48_label_sanity():
    for slot, (emoji, label) in EBI48_CLOCK.items():
        assert isinstance(emoji, str)
        assert isinstance(label, str)
        assert emoji.strip() != "", f"Empty emoji at slot {slot}"
        assert label.strip() != "", f"Empty label at slot {slot}"
