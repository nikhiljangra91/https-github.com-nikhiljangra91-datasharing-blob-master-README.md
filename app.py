import os
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

from categorizer import categorize
from models import Transaction, db
from parser import parse_message

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'transactions.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/parse", methods=["POST"])
def api_parse():
    """Parse an SMS message and return extracted data (preview only, not saved)."""
    body = request.get_json(silent=True) or {}
    message = (body.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    result = parse_message(message)
    if result is None:
        return jsonify({"error": "Could not parse a transaction from this message"}), 422

    result["category"] = categorize(result.get("merchant"), message)
    if result.get("date"):
        result["date"] = result["date"].isoformat()
    return jsonify(result)


@app.route("/api/transactions", methods=["GET"])
def api_list_transactions():
    """List saved transactions with optional filters."""
    month = request.args.get("month")       # YYYY-MM
    account = request.args.get("account")   # last 4 digits
    category = request.args.get("category")
    txn_type = request.args.get("type")     # debit | credit

    query = Transaction.query.order_by(Transaction.date.desc(), Transaction.created_at.desc())

    if month:
        try:
            year, mon = int(month[:4]), int(month[5:7])
            from calendar import monthrange
            last_day = monthrange(year, mon)[1]
            start = datetime(year, mon, 1)
            end = datetime(year, mon, last_day, 23, 59, 59)
            query = query.filter(Transaction.date >= start, Transaction.date <= end)
        except (ValueError, IndexError):
            pass

    if account:
        query = query.filter(Transaction.account_number == account)
    if category:
        query = query.filter(Transaction.category == category)
    if txn_type:
        query = query.filter(Transaction.transaction_type == txn_type)

    transactions = query.all()
    return jsonify([t.to_dict() for t in transactions])


@app.route("/api/transactions", methods=["POST"])
def api_save_transaction():
    """Save a parsed (or manually entered) transaction."""
    body = request.get_json(silent=True) or {}

    raw_message = (body.get("raw_message") or "").strip()
    if not raw_message:
        return jsonify({"error": "raw_message is required"}), 400

    amount = body.get("amount")
    if amount is None:
        return jsonify({"error": "amount is required"}), 400

    date_val = None
    if body.get("date"):
        try:
            date_val = datetime.fromisoformat(body["date"])
        except ValueError:
            pass

    merchant = body.get("merchant") or None
    category = body.get("category") or categorize(merchant, raw_message)

    txn = Transaction(
        account_number=body.get("account_number"),
        account_type=body.get("account_type", "bank"),
        transaction_type=body.get("transaction_type", "debit"),
        amount=float(amount),
        merchant=merchant,
        date=date_val,
        balance=body.get("balance"),
        category=category,
        raw_message=raw_message,
    )
    db.session.add(txn)
    db.session.commit()
    return jsonify(txn.to_dict()), 201


@app.route("/api/transactions/<int:txn_id>", methods=["DELETE"])
def api_delete_transaction(txn_id):
    txn = db.session.get(Transaction, txn_id)
    if txn is None:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(txn)
    db.session.commit()
    return jsonify({"deleted": txn_id})


@app.route("/api/summary", methods=["GET"])
def api_summary():
    """
    Return monthly spending totals by category plus latest balance per account.
    Query param: month=YYYY-MM (defaults to current month)
    """
    month = request.args.get("month")
    if not month:
        now = datetime.now(timezone.utc)
        month = now.strftime("%Y-%m")

    try:
        year, mon = int(month[:4]), int(month[5:7])
        from calendar import monthrange
        last_day = monthrange(year, mon)[1]
        start = datetime(year, mon, 1)
        end = datetime(year, mon, last_day, 23, 59, 59)
    except (ValueError, IndexError):
        return jsonify({"error": "Invalid month format, use YYYY-MM"}), 400

    transactions = (
        Transaction.query
        .filter(Transaction.date >= start, Transaction.date <= end)
        .all()
    )

    # Category totals (debit only for spending)
    category_totals: dict[str, float] = {}
    for t in transactions:
        if t.transaction_type == "debit":
            category_totals[t.category] = category_totals.get(t.category, 0) + t.amount

    total_debit = sum(
        t.amount for t in transactions if t.transaction_type == "debit"
    )
    total_credit = sum(
        t.amount for t in transactions if t.transaction_type == "credit"
    )

    # Latest balance per account
    account_balances: dict[str, dict] = {}
    for t in sorted(transactions, key=lambda x: (x.date or datetime.min)):
        if t.account_number and t.balance is not None:
            account_balances[t.account_number] = {
                "account_number": t.account_number,
                "account_type": t.account_type,
                "balance": t.balance,
            }

    return jsonify({
        "month": month,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "category_totals": category_totals,
        "account_balances": list(account_balances.values()),
        "transaction_count": len(transactions),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
