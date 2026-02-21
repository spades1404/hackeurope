"""Deterministic transaction-to-invoice matching engine.

Provides two scoring functions:

1. pre_filter_score()  — cheap metadata-only score used BEFORE OCR to rank
                          email candidates by how likely they match a transaction.
                          Inputs: email sender, subject, date.

2. score_match()       — full weighted match after OCR extraction.
                          Inputs: transaction + extracted invoice data.
                          5 signals: amount, vendor name, date, reference, IBAN.
"""

import logging
import re
import uuid
from datetime import date
from difflib import SequenceMatcher

import config
from schemas import (
    EmailCandidate,
    ExtractedInvoiceData,
    MatchProposal,
    MatchStatus,
    Transaction,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

# Business entity suffixes to strip before name comparison
ENTITY_SUFFIXES = {
    # English
    "llc", "ltd", "limited", "inc", "incorporated", "corp", "corporation",
    "plc", "llp", "lp", "co", "company", "group", "holdings", "international",
    # German (kept for mixed-language invoices)
    "gmbh", "ag", "kg", "ohg", "ug", "mbh", "e.k.", "e.v.", "gbr",
    # Generic
    "&", "and", "the",
}

# Subject-line keywords strongly associated with invoices / billing emails
INVOICE_SUBJECT_KEYWORDS = {
    "invoice", "receipt", "billing", "bill", "statement",
    "order confirmation", "payment confirmation", "payment receipt",
    "purchase", "charges", "subscription", "renewal", "tax invoice",
}

# ---------------------------------------------------------------------------
# Pre-filter scoring (metadata only, no OCR)
# ---------------------------------------------------------------------------

# Weights for the pre-filter signals (sum = 1.0)
_PRE_FILTER_WEIGHTS = {
    "sender_domain": 0.50,
    "subject_invoice_kw": 0.20,
    "subject_vendor": 0.20,
    "date_proximity": 0.10,
}


def pre_filter_score(
    transaction: Transaction,
    candidate: EmailCandidate,
) -> tuple[float, list[str]]:
    """Score an email candidate using only metadata (no OCR).

    Returns:
        (score 0.0–1.0, list of human-readable reasons)
    """
    reasons: list[str] = []

    # 1. Sender domain vs counterparty name
    domain_score = _score_sender_domain(candidate.email_from, transaction.counterparty_name)
    if domain_score >= 0.5:
        reasons.append(f"Sender likely matches vendor: {candidate.email_from}")

    # 2. Subject line invoice keywords
    subject_lower = candidate.email_subject.lower()
    has_invoice_kw = any(kw in subject_lower for kw in INVOICE_SUBJECT_KEYWORDS)
    kw_score = 1.0 if has_invoice_kw else 0.0
    if has_invoice_kw:
        reasons.append(f"Invoice keyword in subject: '{candidate.email_subject}'")

    # 3. Subject contains vendor name words
    vendor_score = _score_name_in_text(candidate.email_subject, transaction.counterparty_name)
    if vendor_score >= 0.5:
        reasons.append(f"Vendor name found in subject")

    # 4. Date proximity (email should be before or on the transaction date)
    date_score = _score_pre_filter_date(candidate.email_date, transaction.date)

    # Penalise candidates without a PDF — they can't produce a match
    if not candidate.has_pdf:
        return 0.0, ["No PDF attachment"]

    total = (
        _PRE_FILTER_WEIGHTS["sender_domain"] * domain_score
        + _PRE_FILTER_WEIGHTS["subject_invoice_kw"] * kw_score
        + _PRE_FILTER_WEIGHTS["subject_vendor"] * vendor_score
        + _PRE_FILTER_WEIGHTS["date_proximity"] * date_score
    )

    return round(total, 3), reasons


def _score_sender_domain(email_from: str, counterparty_name: str) -> float:
    """Score how well the sender domain matches the counterparty name.

    Extracts the domain (e.g. 'stripe.com' → 'stripe') and compares to the
    key words in the counterparty name.
    """
    # Extract domain root: "billing@aws.amazon.com" → "amazon"
    match = re.search(r"@([\w.-]+)", email_from)
    if not match:
        return 0.0

    domain_parts = match.group(1).lower().split(".")
    # Drop generic TLD and common subdomains; keep the registered domain label
    # e.g. ['mail', 'stripe', 'com'] → focus on 'stripe'
    meaningful_parts = [p for p in domain_parts if p not in {"com", "net", "org", "io", "co", "mail", "www", "email", "noreply", "no-reply"}]
    if not meaningful_parts:
        return 0.0
    domain_root = meaningful_parts[-1]  # last meaningful label = registered domain

    # Compare domain root against counterparty name tokens
    name_tokens = _name_tokens(counterparty_name)
    if not name_tokens:
        return 0.0

    best = max(
        SequenceMatcher(None, domain_root, token).ratio()
        for token in name_tokens
    )

    # Exact token match → strong signal
    if domain_root in name_tokens:
        return 1.0

    return best


def _score_name_in_text(text: str, name: str) -> float:
    """Score how many key name tokens appear in text (case-insensitive)."""
    tokens = _name_tokens(name)
    if not tokens:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for t in tokens if t in text_lower)
    return hits / len(tokens)


def _score_pre_filter_date(email_date, txn_date: date) -> float:
    """Score email date relative to transaction date.

    Invoices are typically issued before payment, so emails sent 0-30 days
    before the transaction score highest.
    """
    try:
        email_d = email_date.date() if hasattr(email_date, "date") else email_date
    except Exception:
        return 0.0

    days_diff = (txn_date - email_d).days  # positive = email before transaction

    if 0 <= days_diff <= 14:
        return 1.0
    if 15 <= days_diff <= 30:
        return 0.8
    if 31 <= days_diff <= 60:
        return 0.5
    if -3 <= days_diff < 0:
        # Email arrived slightly after transaction (e.g., same-day processing)
        return 0.7
    return 0.1


def _name_tokens(name: str) -> list[str]:
    """Lowercase alphabetic tokens from a company name, stripping entity suffixes."""
    tokens = re.findall(r"[a-z0-9]+", name.lower())
    return [t for t in tokens if t not in ENTITY_SUFFIXES and len(t) > 1]


# ---------------------------------------------------------------------------
# Full match scoring (after OCR)
# ---------------------------------------------------------------------------

# Signal weights (sum = 1.0)
WEIGHTS = {
    "amount": 0.40,
    "vendor": 0.25,
    "date": 0.15,
    "reference": 0.10,
    "iban": 0.10,
}


def score_match(
    transaction: Transaction,
    invoice: ExtractedInvoiceData,
) -> MatchProposal:
    """Score how well an extracted invoice matches a transaction.

    Returns a MatchProposal with confidence score and detailed reasons.
    """
    reasons = []

    # --- Amount (40%) ---
    amount_score = 0.0
    amount_match = False
    if invoice.gross_amount is not None:
        txn_amt = abs(transaction.amount)
        inv_amt = abs(invoice.gross_amount)

        if txn_amt > 0 and inv_amt > 0:
            diff_pct = abs(txn_amt - inv_amt) / max(txn_amt, inv_amt)

            if abs(txn_amt - inv_amt) < 0.01:
                amount_score, amount_match = 1.0, True
                reasons.append(f"Exact amount: {transaction.currency}{txn_amt:.2f}")
            elif diff_pct <= 0.01:
                amount_score, amount_match = 0.95, True
                reasons.append(f"Amount within 1%: {txn_amt:.2f} ↔ {inv_amt:.2f}")
            elif invoice.net_amount and abs(txn_amt - abs(invoice.net_amount)) < 0.01:
                amount_score = 0.70
                reasons.append(f"Transaction matches net amount: {txn_amt:.2f} ↔ net {invoice.net_amount:.2f}")
            elif diff_pct <= 0.05:
                amount_score = 0.50
                reasons.append(f"Amount within 5%: {txn_amt:.2f} ↔ {inv_amt:.2f}")
            elif diff_pct <= 0.10:
                amount_score = 0.30

    # --- Vendor name (25%) ---
    vendor_score = 0.0
    vendor_match = False
    if invoice.vendor_name:
        txn_name = transaction.counterparty_name.lower().strip()
        inv_name = invoice.vendor_name.lower().strip()

        if txn_name == inv_name:
            vendor_score, vendor_match = 1.0, True
            reasons.append(f"Exact vendor match: {invoice.vendor_name}")
        else:
            ratio = SequenceMatcher(None, txn_name, inv_name).ratio()

            # Substring containment (banks often truncate names)
            if txn_name in inv_name or inv_name in txn_name:
                ratio = max(ratio, 0.85)

            # Word-level overlap ignoring entity suffixes
            txn_words = set(_name_tokens(txn_name))
            inv_words = set(_name_tokens(inv_name))
            if txn_words and inv_words:
                word_overlap = len(txn_words & inv_words) / max(len(txn_words), len(inv_words))
                ratio = max(ratio, word_overlap)

            vendor_score = ratio
            vendor_match = ratio > 0.75
            if vendor_match:
                reasons.append(
                    f"Vendor match ({ratio:.0%}): '{transaction.counterparty_name}' ↔ '{invoice.vendor_name}'"
                )

    # --- Date proximity (15%) ---
    date_score = 0.0
    date_match = False
    if invoice.invoice_date:
        days_diff = (transaction.date - invoice.invoice_date).days

        if days_diff < -7:
            date_score = 0.1  # Transaction way before invoice — unlikely
        elif days_diff < 0:
            date_score = 0.5
        elif days_diff == 0:
            date_score, date_match = 1.0, True
            reasons.append(f"Same date: {transaction.date}")
        elif days_diff <= 14:
            date_score, date_match = 0.9, True
            reasons.append(f"Date within 14 days: txn {transaction.date} ← inv {invoice.invoice_date}")
        elif days_diff <= 30:
            date_score = 0.7
            reasons.append(f"Date within 30 days: txn {transaction.date} ← inv {invoice.invoice_date}")
        elif days_diff <= config.DATE_WINDOW_DAYS:
            date_score = 0.4

    # --- Reference / payment reference (10%) ---
    ref_score = 0.0
    ref_match = False

    if transaction.reference and invoice.invoice_number:
        if invoice.invoice_number.lower() in transaction.reference.lower():
            ref_score, ref_match = 1.0, True
            reasons.append(f"Invoice number '{invoice.invoice_number}' found in reference")

    if not ref_match and transaction.reference and invoice.payment_reference:
        ratio = SequenceMatcher(
            None,
            transaction.reference.lower(),
            invoice.payment_reference.lower(),
        ).ratio()
        ref_score = ratio
        ref_match = ratio > 0.7
        if ref_match:
            reasons.append(f"Reference match ({ratio:.0%})")

    # --- IBAN (10%) ---
    iban_score = 0.0
    iban_match = False
    if transaction.counterparty_iban and invoice.vendor_iban:
        txn_iban = transaction.counterparty_iban.replace(" ", "").upper()
        inv_iban = invoice.vendor_iban.replace(" ", "").upper()
        if txn_iban == inv_iban:
            iban_score, iban_match = 1.0, True
            reasons.append(f"IBAN match: {txn_iban}")

    # --- Weighted total ---
    confidence = (
        WEIGHTS["amount"] * amount_score
        + WEIGHTS["vendor"] * vendor_score
        + WEIGHTS["date"] * date_score
        + WEIGHTS["reference"] * ref_score
        + WEIGHTS["iban"] * iban_score
    )

    # Boost: amount + identity (vendor or IBAN) both strong
    if amount_match and (vendor_match or iban_match):
        confidence = max(confidence, 0.90)
        reasons.append("Boosted: amount + identity match")

    # Determine status
    if confidence >= config.CONFIDENCE_THRESHOLD_AUTO:
        status = MatchStatus.MATCHED
    elif confidence >= config.CONFIDENCE_THRESHOLD_REVIEW:
        status = MatchStatus.NEEDS_REVIEW
    else:
        status = MatchStatus.NO_MATCH

    return MatchProposal(
        id=str(uuid.uuid4()),
        transaction_id=transaction.id,
        email_id="",  # filled in by the agent
        confidence_score=round(confidence, 3),
        match_reasons=reasons,
        amount_match=amount_match,
        date_match=date_match,
        vendor_match=vendor_match,
        reference_match=ref_match,
        iban_match=iban_match,
        status=status,
        extracted_invoice=invoice,
    )
