# calmoji/meeting_slots.py

# 🕒 calmoji anchor slots — always local time 13:30–14:30
# Times are expressed in UTC to align local anchors

# (Region, Start hour, Start minute, End hour, End minute, Local label)
MEETING_SLOTS = [
    ("Auckland", 5, 35, 6, 0, "15:35–16:00 NZST"),  # Slot A
    ("Auckland", 6, 5, 6, 30, "16:05–16:30 NZST"),  # Slot B
    ("Tokyo", 4, 35, 5, 0, "13:35–14:00 JST"),  # Slot A
    ("Tokyo", 5, 5, 5, 30, "14:05–14:30 JST"),  # Slot B
    ("Delhi", 7, 35, 8, 0, "12:35–13:00 IST"),  # Slot A
    ("Delhi", 8, 5, 8, 30, "13:05–13:30 IST"),  # Slot B
    ("Mecca", 10, 35, 11, 0, "13:35–14:00 AST"),  # Slot A
    ("Mecca", 11, 5, 11, 30, "14:05–14:30 AST"),  # Slot B
    ("Brussels", 11, 35, 12, 0, "13:35–14:00 CEST"),  # Slot A
    ("Brussels", 12, 5, 12, 30, "14:05–14:30 CEST"),  # Slot B
    ("Havana", 17, 35, 18, 0, "13:35–14:00 EDT"),  # Slot A
    ("Havana", 18, 5, 18, 30, "14:05–14:30 EDT"),  # Slot B
    ("Seattle", 20, 35, 21, 0, "13:35–14:00 PDT"),  # Slot A
    ("Seattle", 21, 5, 21, 30, "14:05–14:30 PDT"),  # Slot B
]
