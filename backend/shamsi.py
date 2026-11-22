"""
Shamsi (Solar Hijri / Afghan) date helpers.
Wraps jdatetime so the rest of the app never imports it directly.
"""
import jdatetime
from datetime import date, datetime
from typing import Optional

MONTH_NAMES = [
    "حمل", "ثور", "جوزا", "سرطان", "اسد", "سنبله",
    "میزان", "عقرب", "قوس", "جدی", "دلو", "حوت",
]


def today_shamsi() -> str:
    """Return today as a Shamsi string: 1404-01-15"""
    return jdatetime.date.today().strftime("%Y-%m-%d")


def now_shamsi() -> str:
    """Return current datetime as Shamsi string: 1404-01-15 09:30:00"""
    return jdatetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def gregorian_to_shamsi(d: date) -> str:
    """Convert a Python date/datetime to a Shamsi string."""
    if isinstance(d, datetime):
        d = d.date()
    return jdatetime.date.fromgregorian(date=d).strftime("%Y-%m-%d")


def shamsi_to_gregorian(s: str) -> date:
    """Convert a 'YYYY-MM-DD' Shamsi string to a Python date."""
    parts = s.strip().split("-")
    if len(parts) != 3:
        raise ValueError(f"Invalid Shamsi date: {s!r}")
    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    return jdatetime.date(y, m, d).togregorian()


def shamsi_month_name(month: int) -> str:
    """Return the Dari month name for 1-based month number."""
    if not 1 <= month <= 12:
        raise ValueError(f"Month must be 1–12, got {month}")
    return MONTH_NAMES[month - 1]


def shamsi_year_month(s: str) -> tuple[int, int]:
    """Return (year, month) from a 'YYYY-MM-DD' Shamsi string."""
    parts = s.strip().split("-")
    return int(parts[0]), int(parts[1])


def format_shamsi_display(s: Optional[str]) -> str:
    """Format 'YYYY-MM-DD' as '15 حمل 1404' for display."""
    if not s:
        return "—"
    try:
        parts = s.strip().split("-")
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        return f"{d} {MONTH_NAMES[m-1]} {y}"
    except Exception:
        return s
