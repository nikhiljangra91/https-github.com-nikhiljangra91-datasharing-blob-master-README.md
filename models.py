from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(4), nullable=True)
    account_type = db.Column(db.String(20), nullable=False, default="bank")  # "bank" or "credit_card"
    transaction_type = db.Column(db.String(10), nullable=False)  # "debit" or "credit"
    amount = db.Column(db.Float, nullable=False)
    merchant = db.Column(db.String(200), nullable=True)
    date = db.Column(db.DateTime, nullable=True)
    balance = db.Column(db.Float, nullable=True)
    category = db.Column(db.String(50), nullable=False, default="Other")
    raw_message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "account_number": self.account_number,
            "account_type": self.account_type,
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "merchant": self.merchant,
            "date": self.date.isoformat() if self.date else None,
            "balance": self.balance,
            "category": self.category,
            "raw_message": self.raw_message,
            "created_at": self.created_at.isoformat(),
        }
