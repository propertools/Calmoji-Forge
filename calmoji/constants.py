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

# Each layer's calendar name is exactly the calendar name the docs recommend, and is
# the same in every file of the layer (no years, dates or phases), so apps that
# create a calendar on import name it correctly and repeated imports look consistent.
# Every time in calmoji is UTC, so the names don't say so.
CALNAME_PHASES = "🌗 Seasons"
CALNAME_FOCUS = "🧠 Focus — Open"
CALNAME_MEETINGS = "🕒 Meetings — Open"
CALNAME_EBI48 = "🧿 Emoji Clock"

# Size budget for every .ics file calmoji writes. Calendar apps cap imports
# (reported: Google about 1 MB per file, Outlook failing somewhere between 650
# and 700 events, Proton 15,000 events and 10 MB), so each file is kept well
# under all of them. write_events_to_ics raises if a file would exceed either.
MAX_EVENTS_PER_FILE = 600
MAX_BYTES_PER_FILE = 512 * 1024
