"""
routes/__init__.py
------------------
Registers all blueprints with the Flask app.
"""

from routes.dashboard import dashboard_bp
from routes.transactions import transactions_bp
from routes.budgets import budgets_bp
from routes.analytics import analytics_bp
from routes.settings import settings_bp


ALL_BLUEPRINTS = (
    dashboard_bp,
    transactions_bp,
    budgets_bp,
    analytics_bp,
    settings_bp,
)


def register_blueprints(app):
    """Attach every blueprint to the app."""
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)