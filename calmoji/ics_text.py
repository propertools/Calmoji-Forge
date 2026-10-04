# calmoji/ics_text.py

"""
RFC 5545 §3.3.11 TEXT escaping.

A leaf module (it imports nothing from calmoji), so both calmoji.types and
calmoji.ics_writer can use it.
"""

from __future__ import annotations


def escape_ics_text(value: str) -> str:
    r"""
    Escape a string for use as an iCalendar TEXT value (RFC 5545 §3.3.11).

    - a backslash becomes ``\\`` (done first, so the escapes below aren't doubled)
    - a semicolon becomes ``\;`` and a comma becomes ``\,``
    - CRLF, CR and LF each become ``\n``

    After this, a value can never contain a raw line break, so it can't end its own
    content line and start a new one (property injection).

    Use it for TEXT properties only (SUMMARY, DESCRIPTION, COMMENT, NAME, X-WR-CALNAME).
    Don't use it for RRULE, DTSTART, UID, PRODID and other non-TEXT values.
    """
    return (
        value.replace("\\", r"\\")
        .replace(";", r"\;")
        .replace(",", r"\,")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", r"\n")
    )
