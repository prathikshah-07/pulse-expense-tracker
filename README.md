# PULSE — Smart UPI Expense Tracker

> **See your money clearly.**

A retro-futuristic personal finance dashboard built with **Flask + SQLite + SQLAlchemy + Chart.js**.
Built as a college project — no authentication, no real UPI integration, no external APIs.
All data is stored locally in a single SQLite file.

---

## ✨ Features

### Overview (Dashboard)
- Four summary cards: **Total Income · Total Expenses · Remaining Balance · Savings Rate**
- **Cash-flow chart** (income vs expenses, last 6 months)
- **Category doughnut** with legend, amounts, and percentages
- **Budget overview** with live progress bars and status colours
  (violet → normal, amber → warning, pink → exceeded)
- **Recent transactions** table
- **Dynamic insights** generated from real DB calculations
  (top category, closest-to-limit budget, savings health, month-over-month changes)

### Transactions
- Full CRUD (create, edit, delete) with a shared modal
- Search by description/notes
- Filter by type, category, payment method, and date range
- Sort by date or amount (asc/desc)
- Pagination
- Empty states
- Amounts stored as **integer paise** — no floating-point drift

### Budgets
- One budget per category per month (DB-enforced)
- Live usage % recalculated from transactions
- Alert bands: **normal** (<80%) · **warning** (80–100%) · **exceeded** (≥100%)
- Monthly totals: planned / spent / remaining / overall usage

### Analytics
- Income vs expenses trend (line, 6 months)
- Category distribution (doughnut)
- Top 5 spending categories
- Payment-method breakdown (polar area)
- Average daily spend (accounts for elapsed days in the current month)
- All-time savings summary

### Settings
- Default monthly budget
- Configurable warning threshold
- Clear all transactions/budgets
- Reset demo dataset

---

## 🧱 Tech Stack

| Layer     | Tech                                                              |
|-----------|-------------------------------------------------------------------|
| Backend   | Python 3.10+, Flask 3, Flask-SQLAlchemy 3, Flask-WTF (CSRF)       |
| Database  | SQLite (file-based, zero-config)                                  |
| Templates | Jinja2                                                            |
| Styling   | Bootstrap 5 (utilities only) + custom CSS design system           |
| Charts    | Chart.js 4                                                        |
| Icons     | Lucide                                                            |
| Fonts     | Press Start 2P (display) + Inter (body)                           |

---

