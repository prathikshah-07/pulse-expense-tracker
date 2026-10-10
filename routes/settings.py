"""
routes/settings.py
------------------
Settings page: default monthly budget, warning threshold,
clear / reset demo data.
"""

from __future__ import annotations

from flask import (
    Blueprint, render_template, request, jsonify, redirect, url_for, flash
)

from extensions import db
from models import AppSetting, Transaction, Budget
from config import Config
from utils.validators import validate_settings


settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/", methods=["GET"])
def show_settings():
    default_budget = AppSetting.get_int(
        Config.SETTING_DEFAULT_MONTHLY_BUDGET,
        Config.DEFAULT_MONTHLY_BUDGET_PAISE,
    )
    threshold = AppSetting.get_int(
        Config.SETTING_BUDGET_WARNING_THRESHOLD,
        Config.DEFAULT_BUDGET_WARNING_THRESHOLD,
    )
    tx_count = db.session.query(Transaction.id).count()
    budget_count = db.session.query(Budget.id).count()

    return render_template(
        "settings.html",
        page_title="Settings",
        page_description="Preferences and demo data controls.",
        default_budget_paise=default_budget,
        warning_threshold=threshold,
        tx_count=tx_count,
        budget_count=budget_count,
    )


@settings_bp.route("/save", methods=["POST"])
def save_settings():
    cleaned, errors = validate_settings(request.form)

    if errors:
        # Re-render with errors
        default_budget = AppSetting.get_int(
            Config.SETTING_DEFAULT_MONTHLY_BUDGET,
            Config.DEFAULT_MONTHLY_BUDGET_PAISE,
        )
        threshold = AppSetting.get_int(
            Config.SETTING_BUDGET_WARNING_THRESHOLD,
            Config.DEFAULT_BUDGET_WARNING_THRESHOLD,
        )
        return render_template(
            "settings.html",
            page_title="Settings",
            page_description="Preferences and demo data controls.",
            default_budget_paise=default_budget,
            warning_threshold=threshold,
            tx_count=db.session.query(Transaction.id).count(),
            budget_count=db.session.query(Budget.id).count(),
            errors=errors,
            form=request.form,
        ), 400

    AppSetting.set(
        Config.SETTING_DEFAULT_MONTHLY_BUDGET,
        str(cleaned["default_monthly_budget_paise"]),
    )
    AppSetting.set(
        Config.SETTING_BUDGET_WARNING_THRESHOLD,
        str(cleaned["budget_warning_threshold"]),
    )
    db.session.commit()
    flash("Settings saved.", "success")
    return redirect(url_for("settings.show_settings"))


@settings_bp.route("/clear-data", methods=["POST"])
def clear_data():
    """Delete all transactions and budgets (keeps settings)."""
    Budget.query.delete()
    Transaction.query.delete()
    db.session.commit()
    flash("All transactions and budgets cleared.", "success")
    return redirect(url_for("settings.show_settings"))


@settings_bp.route("/reset-demo", methods=["POST"])
def reset_demo():
    """Wipe and re-seed demo data."""
    from seed import reset_demo_data
    reset_demo_data()
    flash("Demo data reset.", "success")
    return redirect(url_for("settings.show_settings"))