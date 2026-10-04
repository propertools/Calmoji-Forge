# tests/test_utils_key_cases.py

import unittest
from datetime import datetime

from calmoji.ebi48 import EBI48_CLOCK, get_emoji_for_time
from calmoji.uid import generate_uid
from calmoji.utils import slugify


class TestUtilsKeyCases(unittest.TestCase):

    def test_slugify_ascii(self):
        assert slugify("Hello World!") == "hello_world"
        assert slugify("Spaces & Symbols") == "spaces_symbols"
        assert slugify(" multiple   spaces ") == "multiple_spaces"

    def test_slugify_unicode(self):
        assert slugify("Café del Mar") == "cafe_del_mar"
        assert slugify("こんにちは世界", allow_unicode=True) == "こんにちは世界"

    def test_generate_uid_format_and_uniqueness(self):
        dt = datetime(2024, 6, 30, 0, 5)
        label = "test-label"
        uid = generate_uid(dt, label)

        self.assertTrue(uid.endswith("@calmoji.local"))
        self.assertIn("-", uid)
        hash_part, rest = uid.split("-", 1)
        timestamp_part, domain = rest.split("@", 1)

        self.assertEqual(len(hash_part), 16)
        self.assertTrue(all(c in "0123456789abcdef" for c in hash_part))
        self.assertRegex(timestamp_part, r"\d{8}T\d{6}")
        self.assertEqual(domain, "calmoji.local")

        # Check for uniqueness
        uids = {generate_uid(dt, f"label-{i}") for i in range(100)}
        self.assertEqual(len(uids), 100)

    def test_get_emoji_for_time_within_bounds(self):
        dt = datetime(2024, 6, 30, 0, 5)
        pair = get_emoji_for_time(dt)
        assert pair in EBI48_CLOCK.values()

    def test_get_emoji_for_time_does_not_raise(self):
        try:
            dt = datetime(2024, 6, 30, 0, 5)  # Known mapped
            emoji, label = get_emoji_for_time(dt)
            assert isinstance(emoji, str)
            assert isinstance(label, str)
            assert len(emoji) > 0
        except Exception as e:
            assert False, f"Unexpected exception: {e}"


if __name__ == "__main__":
    unittest.main()
