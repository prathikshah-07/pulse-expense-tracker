"""
utils/validators.py
-------------------
Server-side validation for transaction and budget form data.

Every validator returns a tuple: (cleaned_data, errors).
`errors` is a dict {field: message}. Empty dict means success.
"""

from __future__ import annotations

from datetime import date, datetime

from utils.categories import (
    categories_for_type,
    is_valid_category,
    is_valid_payment_method,
    is_valid_transaction_type,
    EXPENSE_CATEGORIES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_amount_to_paise(raw) -> tuple[int | None, str | None]:
    """
    Parse an amount string like "1250.50" or "1250" into integer paise.
    Returns (paise, error_message).
    """
    if raw is None or str(raw).strip() == "":
        return None, "Amount is required."

    text = str(raw).strip().replace(",", "").replace("₹", "")

    try:
        # Reject scientific notation and non-numeric garbage early.
        value = float(text)
    except (TypeError, ValueError):
        return None, "Amount must be a valid number."

    if value != value:  # NaN
        return None, "Amount must be a valid number."

    if value <= 0:
        return None, "Amount must be greater than zero."

    # Cap at ₹10,00,00,000 (1 billion paise * 100)
    if value > 10_000_000:
        return None, "Amount is unrealistically large."

    # Convert to paise, round to nearest paisa (avoid float drift).
    paise = int(round(value * 100))
    if paise <= 0:
        return None, "Amount must be greater than zero."

    return paise, None


def _parse_date(raw) -> tuple[date | None, str | None]:
    """Parse YYYY-MM-DD into a date. Rejects future dates beyond tomorrow."""
    if not raw or str(raw).strip() == "":
        return None, "Date is required."

    try:
        parsed = datetime.strptime(str(raw).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None, "Date must be in YYYY-MM-DD format."

    if parsed.year < 2000 or parsed.year > 2100:
        return None, "Date year must be between 2000 and 2100."

    return parsed, None


def _clean_str(raw, *, max_len: int, required: bool = True) -> tuple[str, str | None]:
    """Trim and length-check a string field."""
    if raw is None:
        raw = ""
    value = str(raw).strip()

    if required and not value:
        return "", "This field is required."
    if len(value) > max_len:
        return "", f"Must be at most {max_len} characters."
    return value, None


# ---------------------------------------------------------------------------
# Transaction validator
# ---------------------------------------------------------------------------
def validate_transaction(form) -> tuple[dict, dict]:
    """
    Validate a transaction form submission.

    `form` is a Flask request.form (or any dict-like). Expected keys:
        description, amount, transaction_type, category,
        payment_method, transaction_date, notes
    """
    errors: dict[str, str] = {}
    cleaned: dict = {}

    # --- transaction_type ---
    ttype = (form.get("transaction_type") or "").strip().lower()
    if not is_valid_transaction_type(ttype):
        errors["transaction_type"] = "Type must be income or expense."
    cleaned["transaction_type"] = ttype

    # --- description ---
    description, err = _clean_str(form.get("description"), max_len=200)
    if err:
        errors["description"] = err
    cleaned["description"] = description

    # --- amount ---
    amount_paise, err = _parse_amount_to_paise(form.get("amount"))
    if err:
        errors["amount"] = err
    cleaned["amount_paise"] = amount_paise

    # --- category (must match type) ---
    category = (form.get("category") or "").strip()
    if not is_valid_category(category):
        errors["category"] = "Please choose a valid category."
    elif ttype in ("income", "expense") and category not in categories_for_type(ttype):
        errors["category"] = f"Category is not valid for {ttype} transactions."
    cleaned["category"] = category

    # --- payment_method ---
    payment_method = (form.get("payment_method") or "").strip()
    if not is_valid_payment_method(payment_method):
        errors["payment_method"] = "Please choose a valid payment method."
    cleaned["payment_method"] = payment_method

    # --- transaction_date ---
    tx_date, err = _parse_date(form.get("transaction_date"))
    if err:
        errors["transaction_date"] = err
    elif tx_date and tx_date > date.today().replace(year=date.today().year + 1):
        errors["transaction_date"] = "Date is too far in the future."
    cleaned["transaction_date"] = tx_date

    # --- notes (optional) ---
    notes, err = _clean_str(form.get("notes"), max_len=500, required=False)
    if err:
        errors["notes"] = err
    cleaned["notes"] = notes or None

    return cleaned, errors


# ---------------------------------------------------------------------------
# Budget validator
# ---------------------------------------------------------------------------
def validate_budget(form) -> tuple[dict, dict]:
    """
    Validate a budget form submission.

    Expected keys: category, monthly_limit, month, year
    """
    errors: dict[str, str] = {}
    cleaned: dict = {}

    # --- category (expense only) ---
    category = (form.get("category") or "").strip()
    if category not in EXPENSE_CATEGORIES:
        errors["category"] = "Budgets can only be set for expense categories."
    cleaned["category"] = category

    # --- monthly_limit ---
    limit_paise, err = _parse_amount_to_paise(form.get("monthly_limit"))
    if err:
        errors["monthly_limit"] = err
    cleaned["monthly_limit_paise"] = limit_paise

    # --- month ---
    try:
        month = int(form.get("month"))
        if not 1 <= month <= 12:
            raise ValueError
        cleaned["month"] = month
    except (TypeError, ValueError):
        errors["month"] = "Month must be between 1 and 12."

    # --- year ---
    try:
        year = int(form.get("year"))
        if not 2000 <= year <= 2100:
            raise ValueError
        cleaned["year"] = year
    except (TypeError, ValueError):
        errors["year"] = "Year must be between 2000 and 2100."

    return cleaned, errors


# ---------------------------------------------------------------------------
# Settings validator
# ---------------------------------------------------------------------------
def validate_settings(form) -> tuple[dict, dict]:
    """
    Validate settings form. Expected keys:
        default_monthly_budget, budget_warning_threshold
    """
    errors: dict[str, str] = {}
    cleaned: dict = {}

    # --- default monthly budget ---
    budget_paise, err = _parse_amount_to_paise(form.get("default_monthly_budget"))
    if err:
        errors["default_monthly_budget"] = err
    cleaned["default_monthly_budget_paise"] = budget_paise

    # --- warning threshold (1-100) ---
    try:
        threshold = int(form.get("budget_warning_threshold"))
        if not 1 <= threshold <= 100:
            raise ValueError
        cleaned["budget_warning_threshold"] = threshold
    except (TypeError, ValueError):
        errors["budget_warning_threshold"] = "Threshold must be 1-100."

    return cleaned, errors