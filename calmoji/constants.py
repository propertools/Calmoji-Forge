# calmoji/constants.py

"""
Values that must be defined exactly once.

Nothing here is computed from the clock, the host or the user: output stays
byte-for-byte reproducible.
"""

# RFC 5545 §3.6.1 requires DTSTAMP in every VEVENT. calmoji's output is
# deterministic, so every event carries this one fixed value rather than "now".
DTSTAMP = "20260101T000000Z"
