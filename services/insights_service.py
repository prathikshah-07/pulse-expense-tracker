"""
services/insights_service.py
----------------------------
Generate dynamic spending insights from the current database state.

Every sentence is produced from real calculations — nothing is
hardcoded. If insufficient data exists, a graceful fallback is returned.
"""

from __future__ import annotations

from utils.formatters import format_inr, format_percent, format_month_label
from services.finance_service import (
    get_month_totals,
    get_category_breakdown,
    get_previous_month_totals,
)
from services.budget_service import get_budgets_with_usage


def generate_insights(month: int, year: int) -> list[dict]:
    """
    Return a list of insight dicts:
        {"tone": "info"|"success"|"warning"|"danger",
         "icon": "<lucide-name>",
         "title": str,
         "body": str}
    """
    insights: list[dict] = []

    totals = get_month_totals(month, year)
    income = totals["income_paise"]
    expense = totals["expense_paise"]
    savings_rate = totals["savings_rate"]
    tx_count = totals["transaction_count"]
    period = format_month_label(month, year)

    # ------------------------------------------------------------------
    # 1. Highest spending category this month
    # ------------------------------------------------------------------
    categories = get_category_breakdown(month, year, "expense")
    if categories:
        top = categories[0]
        insights.append({
            "tone": "info",
            "icon": "trending-up",
            "title": "Top spending category",
            "body": (
                f"{top['category']} leads {period} at "
                f"{format_inr(top['total_paise'])} "
                f"({format_percent(top['percent'], decimals=1)} of expenses)."
            ),
        })

    # ------------------------------------------------------------------
    # 2. Category closest to its budget limit
    # ------------------------------------------------------------------
    budget_rows = get_budgets_with_usage(month, year)
    if budget_rows:
        closest = budget_rows[0]  # already sorted desc by usage_percent
        if closest["status"] == "exceeded":
            insights.append({
                "tone": "danger",
                "icon": "alert-octagon",
                "title": "Budget exceeded",
                "body": (
                    f"{closest['category']} is over budget by "
                    f"{format_inr(abs(closest['remaining_paise']))} "
                    f"({format_percent(closest['usage_percent'], decimals=1)} used)."
                ),
            })
        elif closest["status"] == "warning":
            insights.append({
                "tone": "warning",
                "icon": "alert-triangle",
                "title": "Approaching limit",
                "body": (
                    f"{closest['category']} is at "
                    f"{format_percent(closest['usage_percent'], decimals=1)} of its "
                    f"budget. {format_inr(closest['remaining_paise'])} left."
                ),
            })

    # ------------------------------------------------------------------
    # 3. Overall monthly budget usage
    # ------------------------------------------------------------------
    total_limit = sum(r["limit_paise"] for r in budget_rows)
    if total_limit:
        overall = round(
            (sum(r["spent_paise"] for r in budget_rows) / total_limit) * 100, 1
        )
        tone = "success" if overall < 80 else ("warning" if overall < 100 else "danger")
        insights.append({
            "tone": tone,
            "icon": "gauge",
            "title": "Monthly budget used",
            "body": (
                f"{format_percent(overall, decimals=1)} of your planned "
                f"{format_inr(total_limit)} budget is used."
            ),
        })

    # ------------------------------------------------------------------
    # 4. Savings rate signal
    # ------------------------------------------------------------------
    if income > 0:
        if savings_rate >= 20:
            insights.append({
                "tone": "success",
                "icon": "piggy-bank",
                "title": "Healthy savings",
                "body": (
                    f"You saved {format_percent(savings_rate, decimals=1)} "
                    f"of income in {period}. Nice work."
                ),
            })
        elif savings_rate >= 0:
            insights.append({
                "tone": "warning",
                "icon": "piggy-bank",
                "title": "Low savings",
                "body": (
                    f"Savings rate is only "
                    f"{format_percent(savings_rate, decimals=1)} for {period}."
                ),
            })
        else:
            insights.append({
                "tone": "danger",
                "icon": "piggy-bank",
                "title": "Overspending",
                "body": (
                    f"Spending exceeds income by "
                    f"{format_inr(abs(income - expense))} in {period}."
                ),
            })
    else:
        insights.append({
            "tone": "info",
            "icon": "info",
            "title": "No income recorded",
            "body": f"No income logged for {period}. Add income to track savings.",
        })

    # ------------------------------------------------------------------
    # 5. Comparison with previous month
    # ------------------------------------------------------------------
    prev = get_previous_month_totals(month, year)
    if prev["expense_paise"] > 0 and expense > 0:
        delta = expense - prev["expense_paise"]
        pct = round(abs(delta) / prev["expense_paise"] * 100, 1)
        if delta > 0:
            insights.append({
                "tone": "warning",
                "icon": "arrow-up-right",
                "title": "Spending up",
                "body": (
                    f"Expenses are {format_percent(pct, decimals=1)} higher "
                    f"than {format_month_label(month - 1 if month > 1 else 12, year if month > 1 else year - 1)}."
                ),
            })
        elif delta < 0:
            insights.append({
                "tone": "success",
                "icon": "arrow-down-right",
                "title": "Spending down",
                "body": (
                    f"Expenses dropped {format_percent(pct, decimals=1)} "
                    f"vs the previous month."
                ),
            })

    # ------------------------------------------------------------------
    # 6. Activity recap
    # ------------------------------------------------------------------
    insights.append({
        "tone": "info",
        "icon": "list",
        "title": "Activity",
        "body": (
            f"{tx_count} transaction{'s' if tx_count != 1 else ''} logged "
            f"in {period}."
        ),
    })

    return insights