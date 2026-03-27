"""
SMS/bank message parser for Indian banks and credit cards.
Supports: HDFC, ICICI, SBI, Axis, Kotak, Yes Bank, and generic formats.
"""

import re
from datetime import datetime
from dateutil import parser as dateutil_parser


# ---------------------------------------------------------------------------
# Compiled regex patterns
# ---------------------------------------------------------------------------

# Amount extraction — handles Rs., INR, ₹ with optional comma-separated digits
_AMOUNT_RE = re.compile(
    r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)

# Account number — last 4 digits after common prefixes
_ACCOUNT_RE = re.compile(
    r"(?:a/c|acct|account|card)\s*[Xx*#]+(\d{3,4})|"
    r"[Xx*#]{2,}(\d{4})",
    re.IGNORECASE,
)

# Available / current balance
_BALANCE_RE = re.compile(
    r"(?:avl\.?\s*bal(?:ance)?|available\s*balance|bal(?:ance)?)\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)

# Date patterns
_DATE_PATTERNS = [
    r"\b(\d{1,2}[-/]\w{3}[-/]\d{4})\b",   # 25-Mar-2026, 25/Mar/2026
    r"\b(\d{1,2}[-/]\w{3}[-/]\d{2})\b",    # 25-Mar-26
    r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b",  # 25-03-2026, 25/03/2026
    r"\b(\d{4}[-/]\d{2}[-/]\d{2})\b",      # 2026-03-25
    r"\b(\d{1,2}\s+\w{3}\s+\d{4})\b",      # 25 Mar 2026
]

# Transaction type keywords
_DEBIT_RE = re.compile(r"\b(debit(?:ed)?|dr\.?|withdrawn|spent|paid|sent)\b", re.IGNORECASE)
_CREDIT_RE = re.compile(r"\b(credit(?:ed)?|cr\.?|received|deposited|refund)\b", re.IGNORECASE)

# Credit card detection
_CC_RE = re.compile(r"\b(credit\s*card|cc\s*txn|credit\s*txn)\b", re.IGNORECASE)

# Merchant / payee extraction patterns (ordered by specificity)
_MERCHANT_PATTERNS = [
    # HDFC: "Info: Amazon."
    re.compile(r"\bInfo:\s*([A-Za-z0-9 &'._/-]+?)(?:\.|$|\s+Avl)", re.IGNORECASE),
    # "at <merchant>" (credit card style)
    re.compile(r"\bat\s+([A-Za-z0-9 &'._/-]+?)(?:\s+on\s|\.|,|$)", re.IGNORECASE),
    # "to <name/UPI VPA>"
    re.compile(r"\bto\s+([A-Za-z0-9@._/-]+?)(?:\s+on\s|\s+via|\.|,|$)", re.IGNORECASE),
    # UPI VPA after "VPA"
    re.compile(r"\bVPA\s+([A-Za-z0-9@._/-]+)", re.IGNORECASE),
    # "towards <merchant>"
    re.compile(r"\btowards\s+([A-Za-z0-9 &'._/-]+?)(?:\.|,|$)", re.IGNORECASE),
    # Tran/txn description after "for"
    re.compile(r"\bfor\s+([A-Za-z][A-Za-z0-9 &'._/-]+?)(?:\.|,|$)", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _clean_amount(raw: str) -> float | None:
    try:
        return float(raw.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _extract_amount(text: str) -> float | None:
    match = _AMOUNT_RE.search(text)
    if match:
        return _clean_amount(match.group(1))
    # Fallback: plain number after debit/credit keyword
    fallback = re.search(
        r"(?:debited|credited|debit|credit)\D{0,5}([\d,]+(?:\.\d{1,2})?)", text, re.IGNORECASE
    )
    if fallback:
        return _clean_amount(fallback.group(1))
    return None


def _extract_account(text: str) -> str | None:
    match = _ACCOUNT_RE.search(text)
    if match:
        return match.group(1) or match.group(2)
    return None


def _extract_balance(text: str) -> float | None:
    match = _BALANCE_RE.search(text)
    if match:
        return _clean_amount(match.group(1))
    return None


def _extract_date(text: str) -> datetime | None:
    for pattern in _DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            raw = match.group(1)
            try:
                return dateutil_parser.parse(raw, dayfirst=True)
            except (ValueError, OverflowError):
                continue
    return None


def _extract_merchant(text: str) -> str | None:
    for pattern in _MERCHANT_PATTERNS:
        match = pattern.search(text)
        if match:
            merchant = match.group(1).strip().strip(".")
            if len(merchant) >= 2:
                return merchant
    return None


def _detect_transaction_type(text: str) -> str:
    if _DEBIT_RE.search(text):
        return "debit"
    # Only treat as credit if an explicit credit keyword appears
    # AND it is not just "credit card" (which is the account type, not direction)
    text_no_cc = re.sub(r"credit\s*card", "", text, flags=re.IGNORECASE)
    if _CREDIT_RE.search(text_no_cc):
        return "credit"
    return "debit"  # default assumption for bank alerts


def _detect_account_type(text: str) -> str:
    if _CC_RE.search(text):
        return "credit_card"
    return "bank"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_message(raw_message: str) -> dict | None:
    """
    Parse a raw bank SMS message and return a structured dict, or None
    if the message doesn't appear to be a bank transaction alert.

    Returned dict keys:
        amount, account_number, account_type, transaction_type,
        merchant, date, balance
    """
    text = raw_message.strip()
    if not text:
        return None

    amount = _extract_amount(text)
    if amount is None:
        return None  # Not a transaction message

    return {
        "amount": amount,
        "account_number": _extract_account(text),
        "account_type": _detect_account_type(text),
        "transaction_type": _detect_transaction_type(text),
        "merchant": _extract_merchant(text),
        "date": _extract_date(text),
        "balance": _extract_balance(text),
    }
