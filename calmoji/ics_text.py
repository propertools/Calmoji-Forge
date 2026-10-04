# calmoji/ics_text.py

"""
RFC 5545 §3.3.11 TEXT escaping.

A leaf module (it imports nothing from calmoji), so both calmoji.types and
calmoji.ics_writer can use it.
"""

from __future__ import annotations

from typing import Optional

# TAB is allowed in TEXT; CR and LF are turned into the \n escape.
_ALLOWED_CONTROL = frozenset("\t\r\n")


def _first_forbidden_control_character(value: str) -> Optional[str]:
    """The first character RFC 5545 doesn't allow in TEXT (a control character), or None."""
    for char in value:
        code = ord(char)
        if (code < 0x20 and char not in _ALLOWED_CONTROL) or code == 0x7F:
            return char
    return None


def escape_ics_text(value: str) -> str:
    r"""
    Escape a string for use as an iCalendar TEXT value (RFC 5545 §3.3.11).

    - a backslash becomes ``\\`` (done first, so the escapes below aren't doubled)
    - a semicolon becomes ``\;`` and a comma becomes ``\,``
    - CRLF, CR and LF each become ``\n``
    - horizontal tab is left as it is

    RFC 5545 allows no other control character in TEXT, so a value containing one
    (U+0000 to U+001F except TAB, CR and LF, or U+007F) raises ValueError naming the
    code point, for example U+0007. Nothing is silently dropped or replaced.

    After this, a value can never contain a raw line break, so it can't end its own
    content line and start a new one (property injection).

    Use it for TEXT properties only (SUMMARY, DESCRIPTION, COMMENT, NAME, X-WR-CALNAME).
    Don't use it for RRULE, DTSTART, UID, PRODID and other non-TEXT values.
    """
    bad = _first_forbidden_control_character(value)
    if bad is not None:
        shown = value if len(value) <= 40 else value[:37] + "..."
        raise ValueError(
            f"TEXT values can't contain control characters (RFC 5545 §3.3.11): found U+{ord(bad):04X} in {shown!r}"
        )

    return (
        value.replace("\\", r"\\")
        .replace(";", r"\;")
        .replace(",", r"\,")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", r"\n")
    )
