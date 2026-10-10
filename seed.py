"""
seed.py
-------
One-time demo data seeder for PULSE.

Called by app.py on first launch. Guarded by AppSetting('db_seeded')
so it never runs twice unless explicitly reset.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from calendar import monthrange

from extensions import db
from models import Transaction, Budget, AppSetting
from config import Config


# ---------------------------------------------------------------------------
# Sample data pools
# ---------------------------------------------------------------------------
_EXPENSE_TEMPLATES = [
    # (description, category, payment_method, min_rupees, max_rupees)
    ("Canteen lunch",            "Food & Dining",     "UPI",           80,  220),
    ("Zomato order",             "Food & Dining",     "UPI",          180,  450),
    ("Chai & snacks",            "Food & Dining",     "Cash",          20,   80),
    ("Metro card top-up",        "Transportation",    "UPI",          100,  300),
    ("Auto to campus",           "Transportation",    "Cash",          40,  120),
    ("Ola ride",                 "Transportation",    "UPI",           90,  280),
    ("Notebook & pens",          "Education",         "Cash",          60,  250),
    ("Reference book",           "Education",         "Card",         250,  900),
    ("Online course",            "Education",         "UPI",          499, 1999),
    ("Stationery haul",          "Shopping",          "UPI",          150,  600),
    ("T-shirt",                  "Shopping",          "Card",         399, 1299),
    ("Movie ticket",             "Entertainment",     "UPI",          150,  400),
    ("Gaming top-up",            "Entertainment",     "UPI",          100,  500),
    ("Mobile recharge",          "Bills & Utilities", "UPI",          199,  399),
    ("Electricity share",        "Bills & Utilities", "Bank Transfer",300,  800),
    ("Netflix subscription",     "Subscriptions",     "Card",         149,  649),
    ("Spotify subscription",     "Subscriptions",     "UPI",          119,  199),
    ("Haircut",                  "Personal Care",     "Cash",         100,  300),
    ("Skincare",                 "Personal Care",     "UPI",          200,  700),
    ("Pharmacy",                 "Healthcare",        "Cash",          80,  400),
    ("Doctor consult",           "Healthcare",        "UPI",          300,  800),
    ("Misc expense",             "Other",             "Cash",          50,  300),
]

_INCOME_TEMPLATES = [
    ("Monthly allowance",   "Allowance",       "Bank Transfer", 5000, 8000),
    ("Scholarship credit",  "Scholarship",     "Bank Transfer", 4000, 10000),
    ("Tutoring income",     "Part-time Work",  "UPI",           500,  2000),
    ("Freelance project",   "Freelance",       "Bank Transfer", 1000, 4000),
    ("Refund received",     "Other Income",    "UPI",           100,  500),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _random_date_in_month(month: int, year: int,
                          not_after: date | None = None) -> date:
    """Random day in the given month, never after `not_after`."""
    last_day = monthrange(year, month)[1]
    first = date(year, month, 1)
    last = date(year, month, last_day)
    if not_after and last > not_after:
        last = not_after
    if last < first:
        last = first
    delta = (last - first).days
    return first + timedelta(days=random.randint(0, delta)) if delta else first


def _months_back(n: int) -> list[tuple[int, int]]:
    """Return (month, year) pairs for the last n months, oldest first."""
    today = date.today()
    result = []
    m, y = today.month, today.year
    for _ in range(n):
        result.append((m, y))
        if m == 1:
            m, y = 12, y - 1
        else:
            m -= 1
    return list(reversed(result))


# ---------------------------------------------------------------------------
# Main seeding routine
# ---------------------------------------------------------------------------
def seed_if_needed() -> bool:
    """
    Seed demo data only if the DB has never been seeded.
    Returns True if data was inserted, False otherwise.
    """
    if AppSetting.get_bool(Config.SETTING_DB_SEEDED, False):
        return False

    # Safety: also skip if there are already transactions (e.g. user
    # imported some data before the flag existed).
    if db.session.query(Transaction.id).first() is not None:
        AppSetting.set(Config.SETTING_DB_SEEDED, "1")
        db.session.commit()
        return False

    _seed_transactions()
    _seed_budgets()
    _seed_default_settings()

    AppSetting.set(Config.SETTING_DB_SEEDED, "1")
    db.session.commit()
    return True


def _seed_transactions():
    """Generate ~25-40 transactions across the last 3 months."""
    months = _months_back(Config.SEED_MONTHS_BACK)
    today = date.today()
    target_count = random.randint(
        Config.SEED_MIN_TRANSACTIONS, Config.SEED_MAX_TRANSACTIONS
    )

    transactions: list[Transaction] = []

    # One allowance per month, dated early in the month.
    for m, y in months:
        tx_date = _random_date_in_month(m, y, not_after=today)
        transactions.append(Transaction(
            description="Monthly allowance",
            amount_paise=random.randint(5000, 8000) * 100,
            transaction_type="income",
            category="Allowance",
            payment_method="Bank Transfer",
            transaction_date=tx_date,
            notes="Demo transaction",
        ))

    # One scholarship in the first (oldest) month.
    m0, y0 = months[0]
    transactions.append(Transaction(
        description="Scholarship credit",
        amount_paise=random.randint(6000, 10000) * 100,
        transaction_type="income",
        category="Scholarship",
        payment_method="Bank Transfer",
        transaction_date=_random_date_in_month(m0, y0, not_after=today),
        notes="Demo transaction",
    ))

    # Occasional freelance / part-time income.
    for _ in range(random.randint(2, 4)):
        m, y = random.choice(months)
        desc, cat, method, lo, hi = random.choice(_INCOME_TEMPLATES[2:])
        transactions.append(Transaction(
            description=desc,
            amount_paise=random.randint(lo, hi) * 100,
            transaction_type="income",
            category=cat,
            payment_method=method,
            transaction_date=_random_date_in_month(m, y, not_after=today),
            notes="Demo transaction",
        ))

    # Expenses to fill up to target_count.
    remaining = max(target_count - len(transactions), 10)
    for _ in range(remaining):
        m, y = random.choice(months)
        desc, cat, method, lo, hi = random.choice(_EXPENSE_TEMPLATES)
        transactions.append(Transaction(
            description=desc,
            amount_paise=random.randint(lo, hi) * 100,
            transaction_type="expense",
            category=cat,
            payment_method=method,
            transaction_date=_random_date_in_month(m, y, not_after=today),
            notes="Demo transaction",
        ))

    # Ensure at least one large expense in the current month.
    current_m, current_y = months[-1]
    transactions.append(Transaction(
        description="Campus fest ticket",
        amount_paise=1500 * 100,
        transaction_type="expense",
        category="Entertainment",
        payment_method="UPI",
        transaction_date=_random_date_in_month(current_m, current_y, not_after=today),
        notes="Demo transaction",
    ))

    db.session.add_all(transactions)
    db.session.flush()  # so IDs are assigned (not required, but tidy)


def _seed_budgets():
    """
    Seed budgets for the current month only.
    Designed so that:
      - 'Food & Dining' is approaching its limit (warning).
      - 'Subscriptions' is exceeded.
      - Others are comfortably under.
    """
    today = date.today()
    m, y = today.month, today.year

    # Values chosen to produce the target statuses given the seeded spend.
    plans = [
        # (category, limit_in_rupees)
        ("Food & Dining",    3000),   # likely warning
        ("Transportation",   2000),
        ("Education",        3000),
        ("Shopping",         2500),
        ("Entertainment",     800),   # lower → likely warning/exceeded
        ("Bills & Utilities",2500),
        ("Subscriptions",     700),   # Netflix + Spotify → likely exceeded
        ("Personal Care",    1000),
        ("Healthcare",       1500),
        ("Other",            1000),
    ]

    for category, limit_rupees in plans:
        budget = Budget(
            category=category,
            monthly_limit_paise=limit_rupees * 100,
            month=m,
            year=y,
        )
        db.session.add(budget)


def _seed_default_settings():
    """Write default preferences if they don't exist yet."""
    if AppSetting.get(Config.SETTING_DEFAULT_MONTHLY_BUDGET) is None:
        AppSetting.set(
            Config.SETTING_DEFAULT_MONTHLY_BUDGET,
            str(Config.DEFAULT_MONTHLY_BUDGET_PAISE),
        )
    if AppSetting.get(Config.SETTING_BUDGET_WARNING_THRESHOLD) is None:
        AppSetting.set(
            Config.SETTING_BUDGET_WARNING_THRESHOLD,
            str(Config.DEFAULT_BUDGET_WARNING_THRESHOLD),
        )


# ---------------------------------------------------------------------------
# Reset / clear (used by Settings page)
# ---------------------------------------------------------------------------
def clear_all_data():
    """Delete all transactions and budgets. Keeps settings."""
    Budget.query.delete()
    Transaction.query.delete()
    db.session.commit()


def reset_demo_data():
    """Wipe everything and re-seed."""
    clear_all_data()
    AppSetting.set(Config.SETTING_DB_SEEDED, "0")
    db.session.commit()
    seed_if_needed()