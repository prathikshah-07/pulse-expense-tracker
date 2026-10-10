"""
routes/analytics.py
-------------------
Analytics page: category distribution, income vs expenses,
spending trend, top categories, payment breakdown,
avg daily spend, savings stats.
"""

from __future__ import annotations

from flask import Blueprint, render_template, request

from services.finance_service import (
    get_month_totals,
    get_category_breakdown,
    get_cashflow_trend,
    get_payment_method_breakdown,
    get_average_daily_spend,
    get_all_time_stats,
)
from utils.formatters import parse_month_param, format_month_full
from utils.categories import CATEGORY_META, PAYMENT_META
from config import Config


analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@analytics_bp.route("/")
def analytics_home():
    month, year = parse_month_param(
        request.args.get("month"), request.args.get("year")
    )

    totals = get_month_totals(month, year)
    categories = get_category_breakdown(month, year, "expense")
    income_categories = get_category_breakdown(month, year, "income")
    cashflow = get_cashflow_trend(
        months_back=Config.ANALYTICS_TREND_MONTHS,
        end_month=month,
        end_year=year,
    )
    payments = get_payment_method_breakdown(month, year)
    avg_daily = get_average_daily_spend(month, year)
    all_time = get_all_time_stats()

    # Chart payloads -------------------------------------------------------
    cat_labels = [c["category"] for c in categories]
    cat_values = [c["total_paise"] for c in categories]
    cat_colors = [
        CATEGORY_META.get(c["category"], {}).get("color", "#A59ABF")
        for c in categories
    ]

    payment_labels = [p["payment_method"] for p in payments]
    payment_values = [p["total_paise"] for p in payments]
    payment_icons = [
        PAYMENT_META.get(p["payment_method"], {}).get("icon", "circle")
        for p in payments
    ]

    trend_labels = [c["label"] for c in cashflow]
    trend_income = [c["income_paise"] for c in cashflow]
    trend_expense = [c["expense_paise"] for c in cashflow]

    return render_template(
        "analytics.html",
        page_title="Analytics",
        page_description="Patterns hiding in your spending — surfaced.",
        month=month,
        year=year,
        period_label=format_month_full(month, year),
        totals=totals,
        categories=categories,
        income_categories=income_categories,
        payments=payments,
        avg_daily_paise=avg_daily,
        all_time=all_time,
        chart_category={
            "labels": cat_labels, "values": cat_values, "colors": cat_colors,
        },
        chart_payment={
            "labels": payment_labels, "values": payment_values,
            "icons": payment_icons,
        },
        chart_trend={
            "labels": trend_labels,
            "income": trend_income,
            "expense": trend_expense,
        },
    )