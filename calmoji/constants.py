# calmoji/constants.py

"""
Values that must be defined exactly once.

Nothing here is computed from the clock, the host or the user: output stays
byte-for-byte reproducible.
"""

# RFC 5545 §3.6.1 requires DTSTAMP in every VEVENT. calmoji's output is
# deterministic, so every event carries this one fixed value rather than "now".
DTSTAMP = "20260101T000000Z"

# Where generated files point people who want to know what EBI48 is.
EBI48_URL = "https://github.com/propertools/Calmoji-Forge/blob/main/EBI48-README.md"

# Calendar names are constant per layer (no years, dates or phases), so repeated
# imports into one calendar look consistent.
CALNAME_PHASES = "🧿 calmoji — Semester Phases (UTC)"
CALNAME_FOCUS = "🧿 calmoji — Focus Blocks (UTC)"
CALNAME_MEETINGS = "🧿 calmoji — Meeting Slots (UTC)"
CALNAME_EBI48 = "🧿 calmoji — EBI48 Clock (UTC)"
