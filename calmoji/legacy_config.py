# calmoji/config.py

from calmoji.calendar_config import (
    DEFAULT_ALIGNMENT,
    get_year_start_date,
)

# 🔁 Slot Generation Settings
SERIES_INTERVAL_WEEKS: int = 3
NUM_SERIES: int = 3
NUM_SLOTS_PER_DAY: int = 8
DAYS_PER_WEEK: int = 5

# 🌏 Optional Regional Slot Support
OCEANIA_SLOTS_ENABLED: bool = False

# 🧪 Output Mode
ENABLE_DRY_RUN: bool = True  # can be overridden in CLI

# 🧭 Calendar Defaults
YEAR_START_DATE = get_year_start_date(DEFAULT_ALIGNMENT)

