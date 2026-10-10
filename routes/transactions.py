"""
routes/transactions.py
----------------------
Transaction list + CRUD + filters + search + sort + pagination.
"""

from __future__ import annotations

from datetime import datetime

from flask import (
    Blueprint, render_template, request, jsonify, redirect, url_for, flash
)
from sqlalchemy import or_

from extensions import db
from models import Transaction
from utils.validators import validate_transaction
from utils.categories import (
    EXPENSE_CATEGORIES, INCOME_CATEGORIES, PAYMENT_METHODS,
    is_valid_category, is_valid_payment_method,
)
from config import Config


transactions_bp = Blueprint(
    "transactions", __name__, url_prefix="/transactions"
)


# ---------------------------------------------------------------------------
# Listing + filters
# ---------------------------------------------------------------------------
@transactions_bp.route("/")
def list_transactions():
    # -- Filter parameters
    q = (request.args.get("q") or "").strip()
    f_type = (request.args.get("type") or "").strip()
    f_category = (request.args.get("category") or "").strip()
    f_payment = (request.args.get("payment") or "").strip()
    f_from = (request.args.get("from") or "").strip()
    f_to = (request.args.get("to") or "").strip()
    sort = (request.args.get("sort") or "date_desc").strip()
    page = max(int(request.args.get("page", 1) or 1), 1)

    # -- Query
    query = Transaction.query

    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Transaction.description.ilike(like),
            Transaction.notes.ilike(like),
        ))

    if f_type in ("income", "expense"):
        query = query.filter(Transaction.transaction_type == f_type)

    if f_category and is_valid_category(f_category):
        query = query.filter(Transaction.category == f_category)

    if f_payment and is_valid_payment_method(f_payment):
        query = query.filter(Transaction.payment_method == f_payment)

    if f_from:
        try:
            query = query.filter(
                Transaction.transaction_date >=
                datetime.strptime(f_from, "%Y-%m-%d").date()
            )
        except ValueError:
            pass

    if f_to:
        try:
            query = query.filter(
                Transaction.transaction_date <=
                datetime.strptime(f_to, "%Y-%m-%d").date()
            )
        except ValueError:
            pass

    # -- Sort
    sort_map = {
        "date_desc":   (Transaction.transaction_date.desc(), Transaction.id.desc()),
        "date_asc":    (Transaction.transaction_date.asc(),  Transaction.id.asc()),
        "amount_desc": (Transaction.amount_paise.desc(),     Transaction.id.desc()),
        "amount_asc":  (Transaction.amount_paise.asc(),      Transaction.id.asc()),
    }
    query = query.order_by(*sort_map.get(sort, sort_map["date_desc"]))

    # -- Pagination
    pagination = query.paginate(
        page=page,
        per_page=Config.TRANSACTIONS_PER_PAGE,
        error_out=False,
    )

    # -- Totals for current filter set
    filtered = pagination.items
    income_total = sum(
        t.amount_paise for t in filtered if t.is_income
    )
    expense_total = sum(
        t.amount_paise for t in filtered if t.is_expense
    )

    return render_template(
        "transactions.html",
        page_title="Transactions",
        page_description="Every rupee in and out — searchable, filterable, yours.",
        pagination=pagination,
        transactions=pagination.items,
        filters={
            "q": q, "type": f_type, "category": f_category,
            "payment": f_payment, "from": f_from, "to": f_to, "sort": sort,
        },
        income_total=income_total,
        expense_total=expense_total,
    )


# ---------------------------------------------------------------------------
# Create / update / delete (JSON API used by the modal)
# ---------------------------------------------------------------------------
@transactions_bp.route("/api", methods=["POST"])
def api_create():
    cleaned, errors = validate_transaction(request.form)
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    tx = Transaction(
        description=cleaned["description"],
        amount_paise=cleaned["amount_paise"],
        transaction_type=cleaned["transaction_type"],
        category=cleaned["category"],
        payment_method=cleaned["payment_method"],
        transaction_date=cleaned["transaction_date"],
        notes=cleaned["notes"],
    )
    db.session.add(tx)
    db.session.commit()
    return jsonify({"ok": True, "transaction": tx.to_dict()}), 201


@transactions_bp.route("/api/<int:tx_id>", methods=["PUT", "POST"])
def api_update(tx_id: int):
    tx = db.session.get(Transaction, tx_id)
    if tx is None:
        return jsonify({"ok": False, "error": "Not found"}), 404

    cleaned, errors = validate_transaction(request.form)
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    tx.description = cleaned["description"]
    tx.amount_paise = cleaned["amount_paise"]
    tx.transaction_type = cleaned["transaction_type"]
    tx.category = cleaned["category"]
    tx.payment_method = cleaned["payment_method"]
    tx.transaction_date = cleaned["transaction_date"]
    tx.notes = cleaned["notes"]
    db.session.commit()
    return jsonify({"ok": True, "transaction": tx.to_dict()})


@transactions_bp.route("/api/<int:tx_id>", methods=["DELETE"])
def api_delete(tx_id: int):
    tx = db.session.get(Transaction, tx_id)
    if tx is None:
        return jsonify({"ok": False, "error": "Not found"}), 404
    db.session.delete(tx)
    db.session.commit()
    return jsonify({"ok": True})


@transactions_bp.route("/api/<int:tx_id>", methods=["GET"])
def api_get(tx_id: int):
    tx = db.session.get(Transaction, tx_id)
    if tx is None:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify({"ok": True, "transaction": tx.to_dict()})