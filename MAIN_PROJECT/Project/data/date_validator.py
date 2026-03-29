"""
date_validator.py
------------------
Purpose: Parses a natural language date string extracted from user input,
resolves it to an actual calendar date, and validates that:
  1. The date is not in the past
  2. The date is not more than 90 days in the future (reasonable booking window)
  3. The date is not a Sunday (hospital closed)

Returns a structured result with the resolved date and any error message.
"""

import re
from datetime import date, timedelta

# Day name → weekday number (Monday=0, Sunday=6)
DAY_NAMES = {
    "monday": 0, "tuesday": 1, "wednesday": 2,
    "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
}

# Month name → month number
MONTH_NAMES = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

MAX_ADVANCE_DAYS = 90  # Can book at most 90 days ahead


def _strip_ordinal(s: str) -> str:
    """Remove ordinal suffixes: '25th' → '25', '1st' → '1'"""
    return re.sub(r'(\d+)(st|nd|rd|th)', r'\1', s.lower().strip())


def parse_date(date_str: str) -> date | None:
    """
    Try to parse a natural language date string into a Python date object.
    Returns None if parsing fails.

    Handles:
      - "today", "tomorrow", "day after tomorrow"
      - "next Monday", "next Friday"
      - "25th December", "December 25", "25 Dec 2026"
      - "2026-03-25", "25/03/2026", "03/25/2026"
    """
    if not date_str:
        return None

    today = date.today()
    s = date_str.lower().strip()
    s = _strip_ordinal(s)

    # ── Relative keywords ──────────────────────────────────────────────────────
    if s == "today":
        return today
    if s == "tomorrow":
        return today + timedelta(days=1)
    if s in ("day after tomorrow", "day after"):
        return today + timedelta(days=2)

    # ── "next <weekday>" ───────────────────────────────────────────────────────
    next_match = re.match(r"next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", s)
    if next_match:
        target_day = DAY_NAMES[next_match.group(1)]
        days_ahead = (target_day - today.weekday() + 7) % 7
        if days_ahead == 0:
            days_ahead = 7  # "next Monday" when today IS Monday means 7 days ahead
        return today + timedelta(days=days_ahead)

    # ── Bare weekday: "monday", "friday" ──────────────────────────────────────
    if s in DAY_NAMES:
        target_day = DAY_NAMES[s]
        days_ahead = (target_day - today.weekday() + 7) % 7
        if days_ahead == 0:
            days_ahead = 7
        return today + timedelta(days=days_ahead)

    # ── DD Month [YYYY]: "25 december", "25 december 2026" ────────────────────
    m = re.match(
        r"(\d{1,2})\s+(january|february|march|april|may|june|july|august|"
        r"september|sept|october|november|december|"
        r"jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)"
        r"(?:\s+(\d{4}))?", s
    )
    if m:
        day   = int(m.group(1))
        month = MONTH_NAMES[m.group(2)]
        year  = int(m.group(3)) if m.group(3) else today.year
        try:
            parsed = date(year, month, day)
            # If the date has passed this year, try next year
            if parsed < today and not m.group(3):
                parsed = date(year + 1, month, day)
            return parsed
        except ValueError:
            return None

    # ── Month DD [YYYY]: "december 25", "dec 25 2026" ─────────────────────────
    m = re.match(
        r"(january|february|march|april|may|june|july|august|"
        r"september|sept|october|november|december|"
        r"jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)"
        r"\s+(\d{1,2})(?:\s+(\d{4}))?", s
    )
    if m:
        month = MONTH_NAMES[m.group(1)]
        day   = int(m.group(2))
        year  = int(m.group(3)) if m.group(3) else today.year
        try:
            parsed = date(year, month, day)
            if parsed < today and not m.group(3):
                parsed = date(year + 1, month, day)
            return parsed
        except ValueError:
            return None

    # ── YYYY-MM-DD ─────────────────────────────────────────────────────────────
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None

    # ── DD/MM/YYYY or MM/DD/YYYY ───────────────────────────────────────────────
    m = re.match(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})", s)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        # Try DD/MM/YYYY first (Indian standard)
        try:
            return date(y, b, a)
        except ValueError:
            pass
        # Try MM/DD/YYYY fallback
        try:
            return date(y, a, b)
        except ValueError:
            return None

    return None


def validate_date(date_str: str):
    """
    Parse and validate an appointment date string.

    Returns a dict:
      {
        "valid": True/False,
        "resolved": date object or None,
        "formatted": "Monday, 30 March 2026" or None,
        "error": error message string or None
      }
    """
    today = date.today()

    resolved = parse_date(date_str)

    if resolved is None:
        return {
            "valid": False,
            "resolved": None,
            "formatted": None,
            "error": (
                f"I couldn't understand the date \"{date_str}\". "
                f"Please say something like \"tomorrow\", \"next Monday\", "
                f"\"25th April\", or \"2026-04-25\"."
            )
        }

    # ── Check: not today or in the past ──────────────────────────────────────
    if resolved <= today:
        if resolved == today:
            return {
                "valid": False,
                "resolved": resolved,
                "formatted": None,
                "error": (
                    f"Same-day bookings are not available. "
                    f"Please choose a date from tomorrow onwards."
                )
            }
        return {
            "valid": False,
            "resolved": resolved,
            "formatted": None,
            "error": (
                f"{resolved.strftime('%d %B %Y')} has already passed. "
                f"Today is {today.strftime('%d %B %Y')}. "
                f"Please choose a future date."
            )
        }

    # ── Check: not too far in future ──────────────────────────────────────────
    if (resolved - today).days > MAX_ADVANCE_DAYS:
        return {
            "valid": False,
            "resolved": resolved,
            "formatted": None,
            "error": (
                f"Sorry, we only accept bookings up to {MAX_ADVANCE_DAYS} days in advance. "
                f"{resolved.strftime('%d %B %Y')} is too far ahead. "
                f"Please choose a date within the next {MAX_ADVANCE_DAYS} days."
            )
        }

    # ── Check: not Sunday ─────────────────────────────────────────────────────
    if resolved.weekday() == 6:
        next_monday = resolved + timedelta(days=1)
        return {
            "valid": False,
            "resolved": resolved,
            "formatted": None,
            "error": (
                f"Sorry, CityCare Hospital is closed on Sundays. "
                f"{resolved.strftime('%d %B %Y')} is a Sunday. "
                f"Would you like to book for Monday {next_monday.strftime('%d %B %Y')} instead?"
            )
        }

    # ── All checks passed ─────────────────────────────────────────────────────
    formatted = resolved.strftime("%A, %d %B %Y")  # e.g. "Monday, 30 March 2026"
    return {
        "valid": True,
        "resolved": resolved,
        "formatted": formatted,
        "error": None
    }
