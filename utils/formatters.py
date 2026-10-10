"""
utils/formatters.py
-------------------
Presentation helpers for money, dates, and percentages.

Money is stored as integer paise throughout the app; these functions
convert to display strings only at the render boundary.
"""

from __future__ import annotations

from datetime import date, datetime
from calendar import month_abbr, month_name


# ---------------------------------------------------------------------------
# Money
# ---------------------------------------------------------------------------
def paise_to_rupees(paise: int | None) -> float:
    """Convert paise to rupees (float). Display-only — never for math."""
    if paise is None:
        return 0.0
    return paise / 100.0


def _indian_grouping(number_str: str) -> str:
    """
    Apply Indian digit grouping: 12,34,567.89 instead of 1,234,567.89.
    `number_str` must be a plain digit string with an optional single '.'.
    """
    if "." in number_str:
        int_part, frac_part = number_str.split(".", 1)
    else:
        int_part, frac_part = number_str, ""

    # Reverse for grouping, insert commas every 2 digits after the first 3.
    reversed_digits = int_part[::-1]
    grouped = []
    for i, ch in enumerate(reversed_digits):
        if i == 3 or (i > 3 and (i - 3) % 2 == 0):
            grouped.append(",")
        grouped.append(ch)
    grouped_int = "".join(grouped)[::-1]

    return grouped_int + ("." + frac_part if frac_part else "")


def format_inr(paise: int | None, *, with_symbol: bool = True,
               decimals: int = 2) -> str:
    """
    Format paise as an Indian-rupee string.

    Examples
    --------
    >>> format_inr(123450)
    '₹1,234.50'
    >>> format_inr(123456789, decimals=0)
    '₹12,34,568'
    >>> format_inr(-50000)
    '-₹500.00'
    >>> format_inr(None)
    '₹0.00'
    """
    if paise is None:
        paise = 0

    sign = "-" if paise < 0 else ""
    absolute = abs(int(paise))

    whole = absolute // 100
    frac = absolute % 100

    if decimals <= 0:
        # Round to nearest rupee.
        if frac >= 50:
            whole += 1
        num_str = str(whole)
    else:
        # Clamp to 2 decimals max — paise has 2-digit precision.
        decimals = min(decimals, 2)
        if decimals == 2:
            frac_str = f"{frac:02d}"
        else:  # decimals == 1
            frac_str = f"{frac // 10}"
        num_str = f"{whole}.{frac_str}"

    grouped = _indian_grouping(num_str)
    prefix = "₹" if with_symbol else ""
    return f"{sign}{prefix}{grouped}"


def format_inr_compact(paise: int | None) -> str:
    """
    Short form for tight UI areas (summary cards on mobile).

    Examples
    --------
    >>> format_inr_compact(150000)
    '₹1.5K'
    >>> format_inr_compact(25000000)
    '₹2.5L'
    >>> format_inr_compact(1500000000)
    '₹1.5Cr'
    """
    if paise is None:
        paise = 0

    sign = "-" if paise < 0 else ""
    rupees = abs(paise) / 100.0

    if rupees >= 10_000_000:      # 1 crore
        return f"{sign}₹{rupees / 10_000_000:.2f}Cr"
    if rupees >= 100_000:         # 1 lakh
        return f"{sign}₹{rupees / 100_000:.2f}L"
    if rupees >= 1_000:
        return f"{sign}₹{rupees / 1_000:.1f}K"
    return f"{sign}₹{rupees:.0f}"


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------
def format_date(value: date | datetime | None) -> str:
    """Format a date as '12 Oct 2025'."""
    if value is None:
        return ""
    return value.strftime("%d %b %Y")


def format_date_short(value: date | datetime | None) -> str:
    """Format a date as '12 Oct'."""
    if value is None:
        return ""
    return value.strftime("%d %b")


def format_date_input(value: date | datetime | None) -> str:
    """Format a date for <input type='date'> — YYYY-MM-DD."""
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d")


def format_month_label(month: int, year: int) -> str:
    """'Jan 2025' style label."""
    if not (1 <= month <= 12):
        return f"{month}/{year}"
    return f"{month_abbr[month]} {year}"


def format_month_full(month: int, year: int) -> str:
    """'January 2025'."""
    if not (1 <= month <= 12):
        return f"{month}/{year}"
    return f"{month_name[month]} {year}"


# ---------------------------------------------------------------------------
# Numbers
# ---------------------------------------------------------------------------
def format_percent(value: float | int | None, decimals: int = 0) -> str:
    """
    Format a percentage value.

    >>> format_percent(72.345)
    '72%'
    >>> format_percent(72.345, decimals=1)
    '72.3%'
    """
    if value is None:
        return "0%"
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "0%"
    return f"{num:.{decimals}f}%"


def format_count(value: int | None) -> str:
    """'1 transaction' vs '5 transactions' — tiny helper."""
    if value is None:
        value = 0
    return f"{value} transaction" + ("" if value == 1 else "s")


# ---------------------------------------------------------------------------
# Month-period helpers used by the top-bar selector and services
# ---------------------------------------------------------------------------
def current_month_year() -> tuple[int, int]:
    """Return (month, year) for today."""
    today = date.today()
    return today.month, today.year


def parse_month_param(month_str: str | None, year_str: str | None
                      ) -> tuple[int, int]:
    """
    Parse ?month=&year= query params into (month, year) with safe fallback
    to the current month. Never raises.
    """
    fallback = current_month_year()
    try:
        month = int(month_str) if month_str else fallback[0]
        year = int(year_str) if year_str else fallback[1]
        if not (1 <= month <= 12):
            return fallback
        if not (2000 <= year <= 2100):
            return fallback
        return month, year
    except (TypeError, ValueError):
        return fallback