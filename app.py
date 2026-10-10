"""
app.py
------
Application factory and entry point for PULSE.

Run with:  python app.py
CLI:
    flask --app app init-db
    flask --app app seed
    flask --app app reset-demo
"""

from __future__ import annotations

from flask import Flask, jsonify

from config import get_config, INSTANCE_DIR
from extensions import db, csrf
from routes import register_blueprints
from utils.categories import (
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    ALL_CATEGORIES,
    PAYMENT_METHODS,
    PAYMENT_META,
    CATEGORY_META,
    CATEGORY_COLORS,
    CATEGORY_ICONS,
    get_category_meta,
    get_payment_meta,
    categories_for_type,
)
from utils.formatters import (
    format_inr,
    format_inr_compact,
    format_date,
    format_date_short,
    format_date_input,
    format_month_label,
    format_month_full,
    format_percent,
    current_month_year,
)


def create_app(config_name: str | None = None) -> Flask:
    """Build and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(get_config(config_name))

    # Make sure instance/ exists for SQLite.
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

    # --- Extensions -------------------------------------------------------
    db.init_app(app)
    csrf.init_app(app)

    # --- Models (import so SQLAlchemy sees them) --------------------------
    with app.app_context():
        from models import Transaction, Budget, AppSetting  # noqa: F401

    # --- Blueprints -------------------------------------------------------
    register_blueprints(app)

    # --- Jinja globals + filters -----------------------------------------
    _register_template_helpers(app)

    # --- Error handlers ---------------------------------------------------
    _register_error_handlers(app)

    # --- CLI commands -----------------------------------------------------
    _register_cli(app)

    # --- First-launch bootstrap ------------------------------------------
    with app.app_context():
        db.create_all()
        from seed import seed_if_needed
        seed_if_needed()

    return app


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------
def _register_template_helpers(app: Flask):
    """Expose categories, formatters, and metadata to every template."""

    # Global objects accessible as {{ VAR }} in any template.
    app.jinja_env.globals.update(
        EXPENSE_CATEGORIES=EXPENSE_CATEGORIES,
        INCOME_CATEGORIES=INCOME_CATEGORIES,
        ALL_CATEGORIES=ALL_CATEGORIES,
        PAYMENT_METHODS=PAYMENT_METHODS,
        PAYMENT_META=PAYMENT_META,
        CATEGORY_META=CATEGORY_META,
        CATEGORY_COLORS=CATEGORY_COLORS,
        CATEGORY_ICONS=CATEGORY_ICONS,
        get_category_meta=get_category_meta,
        get_payment_meta=get_payment_meta,
        categories_for_type=categories_for_type,
    )

    # Filters used like: {{ amount|inr }}
    app.jinja_env.filters["inr"] = format_inr
    app.jinja_env.filters["inr_compact"] = format_inr_compact
    app.jinja_env.filters["date_fmt"] = format_date
    app.jinja_env.filters["date_short"] = format_date_short
    app.jinja_env.filters["date_input"] = format_date_input
    app.jinja_env.filters["month_label"] = format_month_label
    app.jinja_env.filters["month_full"] = format_month_full
    app.jinja_env.filters["percent"] = format_percent


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
def _register_error_handlers(app: Flask):
    """Return JSON for API-style routes, otherwise redirect to Overview."""

    @app.errorhandler(404)
    def not_found(e):
        from flask import request, render_template
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "Not found"}), 404
        return render_template("dashboard.html",
                               not_found=True,
                               page_title="Not found",
                               page_description="That page doesn't exist."), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import request
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "Server error"}), 500
        return "Internal server error", 500

    @app.errorhandler(400)
    def bad_request(e):
        from flask import request
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "Bad request"}), 400
        return "Bad request", 400


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _register_cli(app: Flask):

    @app.cli.command("init-db")
    def init_db():
        """Create tables and seed demo data if empty."""
        from seed import seed_if_needed
        db.create_all()
        inserted = seed_if_needed()
        print("Tables ready. Demo data inserted." if inserted
              else "Tables ready. Demo data already present.")

    @app.cli.command("seed")
    def seed_cmd():
        """Force seed demo data (skips if already seeded)."""
        from seed import seed_if_needed
        inserted = seed_if_needed()
        print("Seeded." if inserted else "Already seeded — no changes.")

    @app.cli.command("reset-demo")
    def reset_demo_cmd():
        """Clear all transactions/budgets and re-seed demo data."""
        from seed import reset_demo_data
        reset_demo_data()
        print("Demo data reset.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)