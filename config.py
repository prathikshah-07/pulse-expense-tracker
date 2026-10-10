"""
config.py
---------
Central configuration for the PULSE expense tracker.

Defines configuration classes used by the application factory.
All secrets/paths come from environment variables with safe
development defaults so the project runs out-of-the-box.
"""

import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"


# ---------------------------------------------------------------------------
# Base configuration
# ---------------------------------------------------------------------------
class Config:
    """Base configuration shared by all environments."""

    # --- Core Flask -------------------------------------------------------
    SECRET_KEY = os.environ.get(
        "PULSE_SECRET_KEY",
        "dev-only-secret-change-me-before-production",
    )

    # --- Database ---------------------------------------------------------
    # SQLite database lives inside instance/ so it isn't tracked by git.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "PULSE_DATABASE_URI",
        f"sqlite:///{INSTANCE_DIR / 'pulse.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        # SQLite + Flask dev server: allow the same connection to be
        # used across threads so the CLI seeder and request handlers
        # don't collide.
        "connect_args": {"check_same_thread": False},
    }

    # --- CSRF / Forms -----------------------------------------------------
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # tokens valid for the browser session

    # --- JSON output ------------------------------------------------------
    JSON_SORT_KEYS = False

    # -----------------------------------------------------------------------
    # PULSE application constants
    # These are consumed by services, routes, and templates.
    # -----------------------------------------------------------------------

    # Currency — fixed to Indian Rupee per project spec.
    CURRENCY_CODE = "INR"
    CURRENCY_SYMBOL = "₹"
    # Money is stored as integer paise; this is the conversion factor.
    PAISE_PER_RUPEE = 100

    # Default preferences (overridable at runtime via AppSetting).
    DEFAULT_MONTHLY_BUDGET_PAISE = 15_000 * PAISE_PER_RUPEE  # ₹15,000
    DEFAULT_BUDGET_WARNING_THRESHOLD = 80  # percent

    # Budget alert bands (percent usage).
    BUDGET_WARNING_BAND = (80, 100)   # >=80 and <100  -> approaching
    BUDGET_EXCEEDED_MIN = 100          # >=100           -> exceeded

    # Sanity limits for transaction amounts (in paise).
    MIN_TRANSACTION_PAISE = 1                        # ₹0.01
    MAX_TRANSACTION_PAISE = 100_000_000 * PAISE_PER_RUPEE  # ₹10,00,00,000

    # Pagination defaults for the transactions table.
    TRANSACTIONS_PER_PAGE = 15

    # Number of recent transactions shown on the dashboard.
    DASHBOARD_RECENT_LIMIT = 8

    # How many months of history to use for trend charts.
    ANALYTICS_TREND_MONTHS = 6

    # -----------------------------------------------------------------------
    # AppSetting keys — centralized so we don't typo them anywhere.
    # -----------------------------------------------------------------------
    SETTING_DB_SEEDED = "db_seeded"
    SETTING_DEFAULT_MONTHLY_BUDGET = "default_monthly_budget_paise"
    SETTING_BUDGET_WARNING_THRESHOLD = "budget_warning_threshold"

    # -----------------------------------------------------------------------
    # Seeding
    # -----------------------------------------------------------------------
    # How many months back the demo seeder should populate.
    SEED_MONTHS_BACK = 3
    # Range of transactions to generate (inclusive).
    SEED_MIN_TRANSACTIONS = 25
    SEED_MAX_TRANSACTIONS = 40


# ---------------------------------------------------------------------------
# Environment-specific configurations
# ---------------------------------------------------------------------------
class DevelopmentConfig(Config):
    """Local development configuration."""

    DEBUG = True
    TESTING = False
    # Verbose SQL in dev — flip to False if it gets noisy.
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Configuration used by automated tests."""

    TESTING = True
    DEBUG = False
    # In-memory database for fast, isolated test runs.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Minimal production configuration."""

    DEBUG = False
    TESTING = False


# ---------------------------------------------------------------------------
# Registry — used by app.py to pick a config by name.
# ---------------------------------------------------------------------------
CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(name: str | None = None) -> type[Config]:
    """
    Return the configuration class for the given name.

    Falls back to the FLASK_ENV / PULSE_ENV environment variable, then
    to the development config.
    """
    if name is None:
        name = os.environ.get("PULSE_ENV") or os.environ.get("FLASK_ENV")
    return CONFIG_MAP.get(name or "default", DevelopmentConfig)