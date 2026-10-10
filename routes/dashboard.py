"""
routes/dashboard.py
-------------------
Overview page: summary cards, cashflow chart, category chart,
budget overview, recent transactions, insights.
"""

from __future__ import annotations

from flask import Blueprint, render_template, request

from services.finance_service import (
    get_month_totals,
    get_category_breakdown,
    get_cashflow_trend,
    get_recent_transactions,
)
from services.budget_service import get_budget_summary, get_alert_count
from services.insights_service import generate_insights
from utils.categories import CATEGORY_COLORS, CATEGORY_META
from utils.formatters import (
    parse_month_param,
    format_inr,
    format_month_full,
)
from config import Config


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def overview():
    month, year = parse_month_param(
        request.args.get("month"), request.args.get("year")
    )

    totals = get_month_totals(month, year)
    categories = get_category_breakdown(month, year, "expense")
    cashflow = get_cashflow_trend(
        months_back=Config.ANALYTICS_TREND_MONTHS,
        end_month=month,
        end_year=year,
    )
    budget_summary = get_budget_summary(month, year)
    recent = get_recent_transactions(Config.DASHBOARD_RECENT_LIMIT)
    insights = generate_insights(month, year)
    alert_count = get_alert_count(month, year)

    # Chart.js data -----------------------------------------------------------------
    category_labels = [c["category"] for c in categories]
    category_values_paise = [c["total_paise"] for c in categories]
    category_colors = [
        CATEGORY_META.get(c["category"], {}).get("color", "#A59ABF")
        for c in categories
    ]

    cashflow_labels = [c["label"] for c in cashflow]
    cashflow_income_paise = [c["income_paise"] for c in cashflow]
    cashflow_expense_paise = [c["expense_paise"] for c in cashflow]

    return render_template(
        "dashboard.html",
        page_title="Overview",
        page_description="Your financial snapshot, without the guesswork.",
        month=month,
        year=year,
        period_label=format_month_full(month, year),
        totals=totals,
        categories=categories,
        budget_summary=budget_summary,
        recent=recent,
        insights=insights,
        alert_count=alert_count,
        # Chart payloads
        chart_category={
            "labels": category_labels,
            "values_paise": category_values_paise,
            "colors": category_colors,
        },
        chart_cashflow={
            "labels": cashflow_labels,
            "income_paise": cashflow_income_paise,
            "expense_paise": cashflow_expense_paise,
        },
    )