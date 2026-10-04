# calmoji/focus_blocks_config.py

"""

🧠 Focus Blocks Configuration
-----------------------------
Defines the canonical symbolic layout of focus time blocks across the day.

Each block represents a ~96-minute deep work window, spaced with ~24-minute gaps.
Focus blocks are aligned to UTC and symbolically labeled for intuitive scheduling,
mood anchoring, and cross-cultural continuity.

This configuration powers the weekly focus rituals across all Calmoji phases.

"""

# FOCUS_BLOCKS:
# Format: (Block Number, Start Hour, Start Minute, End Hour, End Minute, Emoji Label)
FOCUS_BLOCKS = [
    (1, 0, 0, 1, 36, "🧠"),  # Deep Thinking
    (2, 2, 0, 3, 36, "✍️"),  # Writing
    (3, 4, 0, 5, 36, "📚"),  # Reading
    (4, 6, 0, 7, 36, "🔧"),  # Technical
    (5, 8, 0, 9, 36, "🧾"),  # Admin / Cleanup
    (6, 10, 0, 11, 36, "📞"),  # Comms / Collab
    (7, 12, 0, 13, 36, "🪞"),  # Reflection
    (8, 14, 0, 15, 36, "📈"),  # Analysis
    (9, 16, 0, 17, 36, "🎨"),  # Creative
    (10, 18, 0, 19, 36, "🛠️"),  # Maintenance
    (11, 20, 0, 21, 36, "⚖️"),  # Decision-making
    (12, 22, 0, 23, 36, "⛩️"),  # Closure / Integration
]

# ACTIVE_WEEKDAYS:
# Optional override for which weekdays focus blocks should be emitted.
# Set to None to use full 7-day week. Use integers: 0 = Monday, 6 = Sunday
#
# Examples:
#   Only weekdays:           ACTIVE_WEEKDAYS = [0, 1, 2, 3, 4]
#   Sunday–Friday (Islamic): ACTIVE_WEEKDAYS = [6, 0, 1, 2, 3, 4]
#   Neurodiverse 3-on/1-off: Implement in future via dynamic mode

ACTIVE_WEEKDAYS = None  # Default behavior: use all 7 days

# Internal fallback if ACTIVE_WEEKDAYS is None
DEFAULT_ACTIVE_WEEKDAYS = list(range(7))  # [0, 1, 2, 3, 4, 5, 6]
