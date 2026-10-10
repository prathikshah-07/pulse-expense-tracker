"""
services/budget_service.py
--------------------------
Budget calculation logic: usage, alerts, remaining, totals.

Budget usage is NEVER stored — it is always derived from the current
transactions in the database, so edits/deletes propagate instantly.
"""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Budget, Transaction, AppSetting
from config import Config
from utils.categories import get_category_meta


# ---------------------------------------------------------------------------
# Status classification
# ---------------------------------------------------------------------------
def classify_usage(percent: float, warning_threshold: int) -> str:
    """
    Return one of: 'normal', 'warning', 'exceeded'.
    `warning_threshold` comes from AppSetting (default 80).
    """
    if percent >= 100:
        return "exceeded"
    if percent >= warning_threshold:
        return "warning"
    return "normal"


def _warning_threshold() -> int:
    """Read the user-configured warning threshold (percent)."""
    return AppSetting.get_int(
        Config.SETTING_BUDGET_WARNING_THRESHOLD,
        Config.DEFAULT_BUDGET_WARNING_THRESHOLD,
    )


# ---------------------------------------------------------------------------
# Category spending for a month
# ---------------------------------------------------------------------------
def _category_spend_map(month: int, year: int) -> dict[str, int]:
    """{category: total_spent_paise} for expense transactions in the month."""
    from calendar import monthrange
    from datetime import date

    first = date(year, month, 1)
    last = date(year, month, monthrange(year, month)[1])

    rows = (
        db.session.query(
            Transaction.category,
            func.coalesce(func.sum(Transaction.amount_paise), 0),
        )
        .filter(
            Transaction.transaction_type == "expense",
            Transaction.transaction_date >= first,
            Transaction.transaction_date <= last,
        )
        .group_by(Transaction.category)
        .all()
    )
    return {cat: int(total) for cat, total in rows}


# ---------------------------------------------------------------------------
# Public: enriched budget rows for a month
# ---------------------------------------------------------------------------
def get_budgets_with_usage(month: int, year: int) -> list[dict]:
    """
    Return every budget for the month, enriched with spending data.

    Each row:
    {
        "id": int,
        "category": str,
        "icon": str,
        "color": str,
        "limit_paise": int,
        "spent_paise": int,
        "remaining_paise": int,     # can be negative if exceeded
        "usage_percent": float,
        "status": "normal" | "warning" | "exceeded",
    }
    """
    budgets = (
        Budget.query
        .filter_by(month=month, year=year)
        .order_by(Budget.category)
        .all()
    )

    spent_map = _category_spend_map(month, year)
    threshold = _warning_threshold()

    result = []
    for b in budgets:
        spent = spent_map.get(b.category, 0)
        limit = b.monthly_limit_paise
        remaining = limit - spent
        percent = round((spent / limit) * 100, 2) if limit else 0.0
        meta = get_category_meta(b.category)

        result.append({
            "id": b.id,
            "category": b.category,
            "icon": meta["icon"],
            "color": meta["color"],
            "limit_paise": limit,
            "spent_paise": spent,
            "remaining_paise": remaining,
            "usage_percent": percent,
            "status": classify_usage(percent, threshold),
        })

    # Show most-at-risk budgets first.
    result.sort(key=lambda r: r["usage_percent"], reverse=True)
    return result


# ---------------------------------------------------------------------------
# Aggregated totals for the month
# ---------------------------------------------------------------------------
def get_budget_summary(month: int, year: int) -> dict:
    """
    Total planned, total spent (only categories with a budget),
    remaining, and overall usage percent.
    """
    rows = get_budgets_with_usage(month, year)

    total_limit = sum(r["limit_paise"] for r in rows)
    total_spent = sum(r["spent_paise"] for r in rows)
    remaining = total_limit - total_spent

    overall_percent = (
        round((total_spent / total_limit) * 100, 2) if total_limit else 0.0
    )

    counts = {"normal": 0, "warning": 0, "exceeded": 0}
    for r in rows:
        counts[r["status"]] += 1

    return {
        "total_limit_paise": total_limit,
        "total_spent_paise": total_spent,
        "remaining_paise": remaining,
        "overall_percent": overall_percent,
        "budget_count": len(rows),
        "warning_count": counts["warning"],
        "exceeded_count": counts["exceeded"],
        "normal_count": counts["normal"],
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Alert count for the topbar bell
# ---------------------------------------------------------------------------
def get_alert_count(month: int, year: int) -> int:
    """Budgets that are warning or exceeded this month."""
    rows = get_budgets_with_usage(month, year)
    return sum(1 for r in rows if r["status"] in ("warning", "exceeded"))


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------
def create_budget(category: str, monthly_limit_paise: int,
                  month: int, year: int) -> tuple[Budget | None, str | None]:
    """
    Create a budget. Returns (budget, error).
    Rejects duplicates for the same (category, month, year).
    """
    existing = Budget.query.filter_by(
        category=category, month=month, year=year
    ).first()
    if existing:
        return None, "A budget for this category and month already exists."

    budget = Budget(
        category=category,
        monthly_limit_paise=monthly_limit_paise,
        month=month,
        year=year,
    )
    db.session.add(budget)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None, "A budget for this category and month already exists."
    return budget, None


def update_budget(budget_id: int, monthly_limit_paise: int
                  ) -> tuple[Budget | None, str | None]:
    """Update the limit on an existing budget."""
    budget = db.session.get(Budget, budget_id)
    if budget is None:
        return None, "Budget not found."

    budget.monthly_limit_paise = monthly_limit_paise
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None, "Could not update budget."
    return budget, None


def delete_budget(budget_id: int) -> tuple[bool, str | None]:
    """Delete a budget by id."""
    budget = db.session.get(Budget, budget_id)
    if budget is None:
        return False, "Budget not found."
    db.session.delete(budget)
    db.session.commit()
    return True, None


def get_unbudgeted_expense_categories(month: int, year: int) -> list[str]:
    """
    Expense categories that have transactions this month but no budget yet.
    Useful for the "Add budget" dropdown.
    """
    from utils.categories import EXPENSE_CATEGORIES

    existing = {
        b.category
        for b in Budget.query.filter_by(month=month, year=year).all()
    }
    return [c for c in EXPENSE_CATEGORIES if c not in existing]