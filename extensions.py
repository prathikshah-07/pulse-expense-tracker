"""
extensions.py
-------------
Central place for Flask extension singletons.

Importing `db` or `csrf` from here (instead of from app.py) avoids
circular imports between the app factory, models, and route blueprints.

Usage in app.py:
    from extensions import db, csrf
    db.init_app(app)
    csrf.init_app(app)
"""

from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


# ---------------------------------------------------------------------------
# SQLAlchemy
# ---------------------------------------------------------------------------
# `db` is the single SQLAlchemy instance used across the entire app.
# - Models subclass db.Model.
# - Services query through db.session.
# - The seeder uses db.session.add_all / commit.
db = SQLAlchemy(
    # Use a stable session options dict so behaviour is consistent
    # across dev / test / prod. `expire_on_commit=False` lets us read
    # attributes from objects after commit without extra queries.
    session_options={
        "expire_on_commit": False,
        "autoflush": True,
    }
)


# ---------------------------------------------------------------------------
# CSRF protection
# ---------------------------------------------------------------------------
# Protects every state-changing POST/PUT/DELETE/PATCH request.
# Tokens are injected into templates via `{{ csrf_token() }}` and into
# JS via a <meta name="csrf-token"> tag written in base.html.
csrf = CSRFProtect()


# ---------------------------------------------------------------------------
# Convenience exports
# ---------------------------------------------------------------------------
__all__ = ["db", "csrf"]