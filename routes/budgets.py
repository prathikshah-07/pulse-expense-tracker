"""
routes/budgets.py
-----------------
Budget management: create, update, delete, view monthly overview.
"""

from __future__ import annotations

from flask import Blueprint, render_template, request, jsonify

from extensions import db
from services.budget_service import (
    get_budget_summary,
    get_budgets_with_usage,
    get_unbudgeted_expense_categories,
    create_budget,
    update_budget,
    delete_budget,
    get_alert_count,
)
from utils.validators import validate_budget
from utils.formatters import parse_month_param, format_month_full
from utils.categories import EXPENSE_CATEGORIES


budgets_bp = Blueprint("budgets", __name__, url_prefix="/budgets")


@budgets_bp.route("/")
def list_budgets():
    month, year = parse_month_param(
        request.args.get("month"), request.args.get("year")
    )
    summary = get_budget_summary(month, year)
    unbudgeted = get_unbudgeted_expense_categories(month, year)

    return render_template(
        "budgets.html",
        page_title="Budgets",
        page_description="Plan your month. Track every limit. Never overspend.",
        month=month,
        year=year,
        period_label=format_month_full(month, year),
        summary=summary,
        rows=summary["rows"],
        unbudgeted=unbudgeted,
        alert_count=get_alert_count(month, year),
    )


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@budgets_bp.route("/api", methods=["POST"])
def api_create():
    cleaned, errors = validate_budget(request.form)
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    budget, err = create_budget(
        category=cleaned["category"],
        monthly_limit_paise=cleaned["monthly_limit_paise"],
        month=cleaned["month"],
        year=cleaned["year"],
    )
    if err:
        return jsonify({"ok": False, "error": err}), 409
    return jsonify({"ok": True, "budget": budget.to_dict()}), 201


@budgets_bp.route("/api/<int:budget_id>", methods=["PUT", "POST"])
def api_update(budget_id: int):
    # Only the limit can change on update.
    try:
        limit_rupees = float(request.form.get("monthly_limit"))
        limit_paise = int(round(limit_rupees * 100))
        if limit_paise <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"ok": False,
                        "errors": {"monthly_limit": "Enter a valid amount."}}), 400

    budget, err = update_budget(budget_id, limit_paise)
    if err:
        return jsonify({"ok": False, "error": err}), 404
    return jsonify({"ok": True, "budget": budget.to_dict()})


@budgets_bp.route("/api/<int:budget_id>", methods=["DELETE"])
def api_delete(budget_id: int):
    ok, err = delete_budget(budget_id)
    if not ok:
        return jsonify({"ok": False, "error": err}), 404
    return jsonify({"ok": True})