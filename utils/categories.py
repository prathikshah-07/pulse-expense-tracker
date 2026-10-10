"""
utils/categories.py
-------------------
Central configuration for transaction categories, payment methods,
and transaction types.

This module is the single source of truth. Nothing else in the
application should hardcode a category name, color, or icon.

Exports
-------
- TRANSACTION_TYPES           : ("income", "expense")
- EXPENSE_CATEGORIES          : tuple of expense category names
- INCOME_CATEGORIES           : tuple of income category names
- ALL_CATEGORIES              : EXPENSE_CATEGORIES + INCOME_CATEGORIES
- PAYMENT_METHODS             : tuple of payment method names
- CATEGORY_META               : dict[str, dict]  -> icon, color, type
- PAYMENT_META                : dict[str, dict]  -> icon, description
- get_category_meta(name)     : safe lookup with a fallback
- get_payment_meta(name)      : safe lookup with a fallback
- categories_for_type(t)     : list of categories for "income"/"expense"
- is_valid_category(name)     : bool
- is_valid_payment_method(m)  : bool
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Transaction types
# ---------------------------------------------------------------------------
TRANSACTION_TYPES: tuple[str, ...] = ("income", "expense")


# ---------------------------------------------------------------------------
# Categories (ordered — order is used by dropdowns and legends)
# ---------------------------------------------------------------------------
EXPENSE_CATEGORIES: tuple[str, ...] = (
    "Food & Dining",
    "Transportation",
    "Shopping",
    "Education",
    "Entertainment",
    "Bills & Utilities",
    "Healthcare",
    "Subscriptions",
    "Personal Care",
    "Other",
)

INCOME_CATEGORIES: tuple[str, ...] = (
    "Allowance",
    "Scholarship",
    "Part-time Work",
    "Freelance",
    "Other Income",
)

ALL_CATEGORIES: tuple[str, ...] = EXPENSE_CATEGORIES + INCOME_CATEGORIES


# ---------------------------------------------------------------------------
# Payment methods
# ---------------------------------------------------------------------------
PAYMENT_METHODS: tuple[str, ...] = (
    "UPI",
    "Cash",
    "Card",
    "Bank Transfer",
)


# ---------------------------------------------------------------------------
# Category metadata
# ---------------------------------------------------------------------------
# `icon`  — Lucide icon name (used with <i data-lucide="...">).
# `color` — hex string used for chart segments, chips, and progress bars.
# `type`  — "expense" or "income" (cross-checked by validators).
#
# Palette choices follow the PULSE design system:
#   violet  #9560FF     bright violet  #B69AFF
#   cyan    #62E7E0     success        #76E5B0
#   warning #FFCA72     danger         #FF718D
#   muted   #A59ABF
# ---------------------------------------------------------------------------
CATEGORY_META: dict[str, dict] = {
    # ---------------------------- Expenses --------------------------------
    "Food & Dining": {
        "icon": "utensils",
        "color": "#FFCA72",
        "type": "expense",
        "description": "Meals, snacks, cafés, food delivery",
    },
    "Transportation": {
        "icon": "bus",
        "color": "#62E7E0",
        "type": "expense",
        "description": "Metro, bus, auto, fuel, ride-hailing",
    },
    "Shopping": {
        "icon": "shopping-bag",
        "color": "#B69AFF",
        "type": "expense",
        "description": "Clothing, gadgets, accessories",
    },
    "Education": {
        "icon": "graduation-cap",
        "color": "#9560FF",
        "type": "expense",
        "description": "Fees, books, courses, stationery",
    },
    "Entertainment": {
        "icon": "gamepad-2",
        "color": "#FF718D",
        "type": "expense",
        "description": "Movies, games, outings, events",
    },
    "Bills & Utilities": {
        "icon": "receipt",
        "color": "#76E5B0",
        "type": "expense",
        "description": "Mobile, electricity, internet, rent",
    },
    "Healthcare": {
        "icon": "heart-pulse",
        "color": "#FF9DB5",
        "type": "expense",
        "description": "Medicines, consultations, check-ups",
    },
    "Subscriptions": {
        "icon": "repeat",
        "color": "#8FD8FF",
        "type": "expense",
        "description": "OTT, music, cloud storage, memberships",
    },
    "Personal Care": {
        "icon": "sparkles",
        "color": "#E0C7FF",
        "type": "expense",
        "description": "Grooming, hygiene, wellness",
    },
    "Other": {
        "icon": "circle-ellipsis",
        "color": "#A59ABF",
        "type": "expense",
        "description": "Anything that doesn't fit the above",
    },

    # ----------------------------- Income ---------------------------------
    "Allowance": {
        "icon": "wallet",
        "color": "#76E5B0",
        "type": "income",
        "description": "Monthly allowance from family",
    },
    "Scholarship": {
        "icon": "award",
        "color": "#62E7E0",
        "type": "income",
        "description": "Scholarships, grants, stipends",
    },
    "Part-time Work": {
        "icon": "briefcase",
        "color": "#9560FF",
        "type": "income",
        "description": "Internships, campus jobs, shifts",
    },
    "Freelance": {
        "icon": "laptop",
        "color": "#B69AFF",
        "type": "income",
        "description": "Freelance gigs, tutoring, commissions",
    },
    "Other Income": {
        "icon": "plus-circle",
        "color": "#8FD8FF",
        "type": "income",
        "description": "Refunds, gifts, one-off credits",
    },
}


# ---------------------------------------------------------------------------
# Payment method metadata
# ---------------------------------------------------------------------------
PAYMENT_META: dict[str, dict] = {
    "UPI": {
        "icon": "smartphone",
        "description": "Unified Payments Interface",
    },
    "Cash": {
        "icon": "banknote",
        "description": "Physical currency",
    },
    "Card": {
        "icon": "credit-card",
        "description": "Debit or credit card",
    },
    "Bank Transfer": {
        "icon": "landmark",
        "description": "NEFT / IMPS / direct transfer",
    },
}


# ---------------------------------------------------------------------------
# Fallbacks — used if a stored value somehow slips past validation.
# ---------------------------------------------------------------------------
_FALLBACK_CATEGORY: dict = {
    "icon": "tag",
    "color": "#A59ABF",
    "type": "expense",
    "description": "Uncategorized",
}

_FALLBACK_PAYMENT: dict = {
    "icon": "circle",
    "description": "Unknown payment method",
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
def get_category_meta(name: str) -> dict:
    """
    Return metadata for a category, or a safe fallback if unknown.

    Never raises — templates can call this without defensive checks.
    """
    return CATEGORY_META.get(name, _FALLBACK_CATEGORY)


def get_payment_meta(name: str) -> dict:
    """Return metadata for a payment method, or a safe fallback."""
    return PAYMENT_META.get(name, _FALLBACK_PAYMENT)


def categories_for_type(transaction_type: str) -> list[str]:
    """
    Return the ordered list of categories for a transaction type.

    Unknown types return an empty list.
    """
    if transaction_type == "expense":
        return list(EXPENSE_CATEGORIES)
    if transaction_type == "income":
        return list(INCOME_CATEGORIES)
    return []


def is_valid_category(name: str) -> bool:
    """True if `name` is one of the known categories."""
    return name in ALL_CATEGORIES


def is_valid_expense_category(name: str) -> bool:
    return name in EXPENSE_CATEGORIES


def is_valid_income_category(name: str) -> bool:
    return name in INCOME_CATEGORIES


def is_valid_payment_method(name: str) -> bool:
    return name in PAYMENT_METHODS


def is_valid_transaction_type(name: str) -> bool:
    return name in TRANSACTION_TYPES


def category_color(name: str) -> str:
    """Shortcut used by Chart.js datasets."""
    return get_category_meta(name)["color"]


def category_icon(name: str) -> str:
    """Shortcut used by Jinja templates."""
    return get_category_meta(name)["icon"]


# ---------------------------------------------------------------------------
# Convenience dictionaries for template rendering
# ---------------------------------------------------------------------------
# Jinja2 gets these via app context processor (wired in app.py).
CATEGORY_COLORS: dict[str, str] = {
    name: meta["color"] for name, meta in CATEGORY_META.items()
}

CATEGORY_ICONS: dict[str, str] = {
    name: meta["icon"] for name, meta in CATEGORY_META.items()
}