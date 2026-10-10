"""
models.py
---------
SQLAlchemy models for PULSE.

Design notes
------------
- All monetary values are stored as INTEGER paise (1 INR = 100 paise).
  This avoids floating-point errors in totals and budget math.
- `Transaction.transaction_date` is a DATE; `created_at`/`updated_at`
  are DATETIMEs maintained automatically.
- `Budget` enforces one row per (category, month, year) via a
  UniqueConstraint, matching the spec.
- `AppSetting` is a simple key/value store for persisting user
  preferences and flags (e.g. db_seeded).
"""

from datetime import date, datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from extensions import db
from utils.categories import (
    ALL_CATEGORIES,
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    PAYMENT_METHODS,
    TRANSACTION_TYPES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _utcnow() -> datetime:
    """Timezone-aware UTC now (used for created_at / updated_at)."""
    return datetime.now(timezone.utc)


# Build SQL-safe comma-separated lists for CHECK constraints.
# These are static (defined in utils/categories.py), so embedding them
# directly in DDL is safe — no user input touches these strings.
def _sql_list(values) -> str:
    return ", ".join(f"'{v}'" for v in values)


_TYPE_CHECK = _sql_list(TRANSACTION_TYPES)
_EXPENSE_CAT_CHECK = _sql_list(EXPENSE_CATEGORIES)
_INCOME_CAT_CHECK = _sql_list(INCOME_CATEGORIES)
_ALL_CAT_CHECK = _sql_list(ALL_CATEGORIES)
_PAYMENT_CHECK = _sql_list(PAYMENT_METHODS)


# ---------------------------------------------------------------------------
# Transaction
# ---------------------------------------------------------------------------
class Transaction(db.Model):
    """A single income or expense record."""

    __tablename__ = "transactions"

    # --- Primary key ------------------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # --- Core fields ------------------------------------------------------
    description: Mapped[str] = mapped_column(String(200), nullable=False)

    # Money in paise. Always positive; sign is derived from transaction_type.
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)

    transaction_type: Mapped[str] = mapped_column(String(16), nullable=False)

    category: Mapped[str] = mapped_column(String(50), nullable=False)

    payment_method: Mapped[str] = mapped_column(String(32), nullable=False)

    transaction_date: Mapped[date] = mapped_column(
        db.Date, nullable=False, default=date.today
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Timestamps -------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    # --- Constraints ------------------------------------------------------
    __table_args__ = (
        CheckConstraint("amount_paise > 0", name="ck_tx_amount_positive"),
        CheckConstraint(
            f"transaction_type IN ({_TYPE_CHECK})",
            name="ck_tx_type_valid",
        ),
        CheckConstraint(
            f"category IN ({_ALL_CAT_CHECK})",
            name="ck_tx_category_valid",
        ),
        CheckConstraint(
            f"payment_method IN ({_PAYMENT_CHECK})",
            name="ck_tx_payment_valid",
        ),
        # Indexes for common filters / sorts.
        Index("ix_tx_date", "transaction_date"),
        Index("ix_tx_type", "transaction_type"),
        Index("ix_tx_category", "category"),
        Index("ix_tx_date_type", "transaction_date", "transaction_type"),
    )

    # --- Convenience properties ------------------------------------------
    @property
    def amount_rupees(self) -> float:
        """Amount in rupees as a float — for display only, never for math."""
        return self.amount_paise / 100.0

    @property
    def is_income(self) -> bool:
        return self.transaction_type == "income"

    @property
    def is_expense(self) -> bool:
        return self.transaction_type == "expense"

    @property
    def signed_amount_paise(self) -> int:
        """Positive for income, negative for expense."""
        return self.amount_paise if self.is_income else -self.amount_paise

    # --- Validation -------------------------------------------------------
    def validate_category_for_type(self) -> bool:
        """Ensure the category belongs to the declared transaction_type."""
        if self.is_income:
            return self.category in INCOME_CATEGORIES
        return self.category in EXPENSE_CATEGORIES

    def to_dict(self) -> dict:
        """Serialize for JSON responses (e.g. edit modal prefill)."""
        return {
            "id": self.id,
            "description": self.description,
            "amount_paise": self.amount_paise,
            "amount_rupees": self.amount_rupees,
            "transaction_type": self.transaction_type,
            "category": self.category,
            "payment_method": self.payment_method,
            "transaction_date": self.transaction_date.isoformat(),
            "notes": self.notes or "",
        }

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} type={self.transaction_type} "
            f"category={self.category!r} amount={self.amount_paise}p>"
        )


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------
class Budget(db.Model):
    """A monthly budget limit for one expense category."""

    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    category: Mapped[str] = mapped_column(String(50), nullable=False)

    # Monthly limit stored in paise.
    monthly_limit_paise: Mapped[int] = mapped_column(Integer, nullable=False)

    # Month (1-12) and year (e.g. 2025).
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    __table_args__ = (
        # One budget per category per month per year.
        UniqueConstraint(
            "category", "month", "year",
            name="uq_budget_category_month_year",
        ),
        CheckConstraint(
            "monthly_limit_paise > 0",
            name="ck_budget_limit_positive",
        ),
        CheckConstraint(
            "month BETWEEN 1 AND 12",
            name="ck_budget_month_range",
        ),
        CheckConstraint(
            "year BETWEEN 2000 AND 2100",
            name="ck_budget_year_range",
        ),
        # Budgets can only apply to expense categories.
        CheckConstraint(
            f"category IN ({_EXPENSE_CAT_CHECK})",
            name="ck_budget_category_expense_only",
        ),
        Index("ix_budget_period", "year", "month"),
    )

    # --- Convenience properties ------------------------------------------
    @property
    def monthly_limit_rupees(self) -> float:
        return self.monthly_limit_paise / 100.0

    @property
    def period_label(self) -> str:
        """e.g. 'Jan 2025'."""
        from calendar import month_abbr  # local import avoids a module cycle
        return f"{month_abbr[self.month]} {self.year}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "monthly_limit_paise": self.monthly_limit_paise,
            "monthly_limit_rupees": self.monthly_limit_rupees,
            "month": self.month,
            "year": self.year,
        }

    def __repr__(self) -> str:
        return (
            f"<Budget id={self.id} category={self.category!r} "
            f"limit={self.monthly_limit_paise}p {self.month}/{self.year}>"
        )


# ---------------------------------------------------------------------------
# AppSetting
# ---------------------------------------------------------------------------
class AppSetting(db.Model):
    """Key/value store for user preferences and internal flags."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    setting_key: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    setting_value: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    # ---------------------------------------------------------------------
    # Static helpers — always go through these so callers don't duplicate
    # the upsert/parse logic.
    # ---------------------------------------------------------------------
    @classmethod
    def get(cls, key: str, default: str | None = None) -> str | None:
        """Fetch a raw string value by key, or `default` if missing."""
        row = cls.query.filter_by(setting_key=key).first()
        return row.setting_value if row else default

    @classmethod
    def set(cls, key: str, value) -> "AppSetting":
        """Insert or update a setting. Returns the persisted row."""
        row = cls.query.filter_by(setting_key=key).first()
        str_value = str(value)
        if row is None:
            row = cls(setting_key=key, setting_value=str_value)
            db.session.add(row)
        else:
            row.setting_value = str_value
        return row

    @classmethod
    def get_int(cls, key: str, default: int) -> int:
        """Fetch and coerce to int, falling back on failure."""
        raw = cls.get(key)
        if raw is None:
            return default
        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def get_bool(cls, key: str, default: bool = False) -> bool:
        """Fetch and coerce to bool. Accepts 1/0/true/false/yes/no."""
        raw = cls.get(key)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    def __repr__(self) -> str:
        return f"<AppSetting {self.setting_key}={self.setting_value!r}>"