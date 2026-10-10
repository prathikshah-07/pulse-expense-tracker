"""
services/finance_service.py
---------------------------
Pure financial calculations over Transaction records.

Every function returns values in integer paise unless stated otherwise.
No ORM objects leak out — callers get plain dicts/lists/numbers.
"""

from __future__ import annotations

from datetime import date, timedelta
from calendar import monthrange
from sqlalchemy import func, extract

from extensions import db
from models import Transaction


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _month_bounds(month: int, year: int) -> tuple[date, date]:
    """Return (first_day, last_day) for the given month/year."""
    first = date(year, month, 1)
    last = date(year, month, monthrange(year, month)[1])
    return first, last


def _previous_month(month: int, year: int) -> tuple[int, int]:
    if month == 1:
        return 12, year - 1
    return month - 1, year


# ---------------------------------------------------------------------------
# Monthly totals
# ---------------------------------------------------------------------------
def get_month_totals(month: int, year: int) -> dict:
    """
    Aggregate income, expense, balance, savings rate, and transaction count
    for the given month.

    Returns
    -------
    {
        "income_paise": int,
        "expense_paise": int,
        "balance_paise": int,
        "savings_rate": float,     # 0-100, safe when income == 0
        "transaction_count": int,
        "month": int,
        "year": int,
    }
    """
    first, last = _month_bounds(month, year)

    rows = (
        db.session.query(
            Transaction.transaction_type,
            func.coalesce(func.sum(Transaction.amount_paise), 0),
            func.count(Transaction.id),
        )
        .filter(
            Transaction.transaction_date >= first,
            Transaction.transaction_date <= last,
        )
        .group_by(Transaction.transaction_type)
        .all()
    )

    income = 0
    expense = 0
    count = 0
    for ttype, total, cnt in rows:
        count += cnt
        if ttype == "income":
            income = int(total)
        elif ttype == "expense":
            expense = int(total)

    balance = income - expense

    if income > 0:
        savings_rate = round((balance / income) * 100, 2)
    else:
        # No income this month — savings rate is undefined. Report 0,
        # and the UI will show a friendly "no income yet" hint.
        savings_rate = 0.0

    return {
        "income_paise": income,
        "expense_paise": expense,
        "balance_paise": balance,
        "savings_rate": savings_rate,
        "transaction_count": count,
        "month": month,
        "year": year,
    }


# ---------------------------------------------------------------------------
# Category breakdown
# ---------------------------------------------------------------------------
def get_category_breakdown(month: int, year: int,
                           transaction_type: str = "expense") -> list[dict]:
    """
    Category totals for a month, sorted descending by amount.

    Returns list of:
        {"category": str, "total_paise": int, "count": int, "percent": float}
    """
    first, last = _month_bounds(month, year)

    rows = (
        db.session.query(
            Transaction.category,
            func.coalesce(func.sum(Transaction.amount_paise), 0),
            func.count(Transaction.id),
        )
        .filter(
            Transaction.transaction_date >= first,
            Transaction.transaction_date <= last,
            Transaction.transaction_type == transaction_type,
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount_paise).desc())
        .all()
    )

    grand_total = sum(int(total) for _, total, _ in rows) or 1  # avoid /0

    result = []
    for cat, total, cnt in rows:
        total = int(total)
        result.append({
            "category": cat,
            "total_paise": total,
            "count": cnt,
            "percent": round((total / grand_total) * 100, 2),
        })
    return result


# ---------------------------------------------------------------------------
# Cash-flow trend (multi-month)
# ---------------------------------------------------------------------------
def get_cashflow_trend(months_back: int = 6,
                       end_month: int | None = None,
                       end_year: int | None = None) -> list[dict]:
    """
    Income vs expenses for the last `months_back` months, oldest first.

    Returns list of:
        {"label": "Jan 2025", "month": 1, "year": 2025,
         "income_paise": int, "expense_paise": int}
    """
    today = date.today()
    end_month = end_month or today.month
    end_year = end_year or today.year

    # Build the (month, year) pairs oldest → newest.
    periods: list[tuple[int, int]] = []
    m, y = end_month, end_year
    for _ in range(months_back):
        periods.append((m, y))
        m, y = _previous_month(m, y)
    periods.reverse()

    from calendar import month_abbr

    result = []
    for m, y in periods:
        totals = get_month_totals(m, y)
        result.append({
            "label": f"{month_abbr[m]} {y}",
            "month": m,
            "year": y,
            "income_paise": totals["income_paise"],
            "expense_paise": totals["expense_paise"],
        })
    return result


# ---------------------------------------------------------------------------
# Payment-method breakdown
# ---------------------------------------------------------------------------
def get_payment_method_breakdown(month: int | None = None,
                                 year: int | None = None) -> list[dict]:
    """
    Expense totals grouped by payment method.
    If month/year are None, covers all time.
    """
    query = db.session.query(
        Transaction.payment_method,
        func.coalesce(func.sum(Transaction.amount_paise), 0),
        func.count(Transaction.id),
    ).filter(Transaction.transaction_type == "expense")

    if month and year:
        first, last = _month_bounds(month, year)
        query = query.filter(
            Transaction.transaction_date >= first,
            Transaction.transaction_date <= last,
        )

    rows = query.group_by(Transaction.payment_method).all()
    grand = sum(int(t) for _, t, _ in rows) or 1

    result = []
    for method, total, cnt in rows:
        total = int(total)
        result.append({
            "payment_method": method,
            "total_paise": total,
            "count": cnt,
            "percent": round((total / grand) * 100, 2),
        })
    result.sort(key=lambda r: r["total_paise"], reverse=True)
    return result


# ---------------------------------------------------------------------------
# Daily / average stats
# ---------------------------------------------------------------------------
def get_average_daily_spend(month: int, year: int) -> int:
    """
    Average daily expense (paise) across the *elapsed* days of the month.
    For a past month, divides by total days. For the current month,
    divides by days elapsed so far.
    """
    first, last = _month_bounds(month, year)
    total = (
        db.session.query(func.coalesce(func.sum(Transaction.amount_paise), 0))
        .filter(
            Transaction.transaction_date >= first,
            Transaction.transaction_date <= last,
            Transaction.transaction_type == "expense",
        )
        .scalar()
    )
    total = int(total or 0)

    today = date.today()
    if today.year == year and today.month == month:
        days = today.day
    else:
        days = monthrange(year, month)[1]

    return total // days if days else 0


# ---------------------------------------------------------------------------
# Recent transactions
# ---------------------------------------------------------------------------
def get_recent_transactions(limit: int = 8) -> list[Transaction]:
    """Newest transactions first (by date, then by id for stability)."""
    return (
        Transaction.query
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .limit(limit)
        .all()
    )


# ---------------------------------------------------------------------------
# Comparison with previous month (for insights)
# ---------------------------------------------------------------------------
def get_previous_month_totals(month: int, year: int) -> dict:
    """Convenience wrapper: totals for the month before the given one."""
    pm, py = _previous_month(month, year)
    return get_month_totals(pm, py)


# ---------------------------------------------------------------------------
# All-time stats (for analytics)
# ---------------------------------------------------------------------------
def get_all_time_stats() -> dict:
    """Total income, expenses, savings across every transaction."""
    income = (
        db.session.query(func.coalesce(func.sum(Transaction.amount_paise), 0))
        .filter(Transaction.transaction_type == "income")
        .scalar()
    ) or 0
    expense = (
        db.session.query(func.coalesce(func.sum(Transaction.amount_paise), 0))
        .filter(Transaction.transaction_type == "expense")
        .scalar()
    ) or 0

    income = int(income)
    expense = int(expense)
    savings = income - expense
    rate = round((savings / income) * 100, 2) if income > 0 else 0.0

    return {
        "income_paise": income,
        "expense_paise": expense,
        "savings_paise": savings,
        "savings_rate": rate,
    }