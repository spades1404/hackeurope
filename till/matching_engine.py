"""Deterministic transaction-to-invoice matching engine.

Scores a match between a transaction and extracted invoice data using
5 weighted signals: amount, vendor name, date, reference, IBAN.
"""

import logging
import uuid
from datetime import timedelta
from difflib import SequenceMatcher

import config
from models.schemas import (
    ExtractedInvoiceData,
    MatchProposal,
    MatchStatus,
    Transaction,
)

logger = logging.getLogger(__name__)

# Signal weights (sum = 1.0)
WEIGHTS = {
    "amount": 0.40,
    "vendor": 0.25,
    "date": 0.15,
    "reference": 0.10,
    "iban": 0.10,
}

# German business entity suffixes to ignore in name comparison
ENTITY_SUFFIXES = {
    "gmbh", "ag", "kg", "ohg", "ug", "e.k.", "mbh", "co.",
    "&", "und", "co", "inc", "ltd", "se", "e.v.", "gbr",
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
                reasons.append(f"Exact amount: €{txn_amt:.2f}")
            elif diff_pct <= 0.01:
                amount_score, amount_match = 0.95, True
                reasons.append(f"Amount within 1%: €{txn_amt:.2f} ↔ €{inv_amt:.2f}")
            elif invoice.net_amount and abs(txn_amt - abs(invoice.net_amount)) < 0.01:
                amount_score = 0.70
                reasons.append(f"Transaction matches net amount: €{txn_amt:.2f} ↔ net €{invoice.net_amount:.2f}")
            elif diff_pct <= 0.05:
                amount_score = 0.50
                reasons.append(f"Amount within 5%: €{txn_amt:.2f} ↔ €{inv_amt:.2f}")
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
            # Fuzzy ratio
            ratio = SequenceMatcher(None, txn_name, inv_name).ratio()

            # Substring containment (banks often truncate names)
            if txn_name in inv_name or inv_name in txn_name:
                ratio = max(ratio, 0.85)

            # Word-level overlap (ignoring entity suffixes)
            txn_words = set(txn_name.split()) - ENTITY_SUFFIXES
            inv_words = set(inv_name.split()) - ENTITY_SUFFIXES
            if txn_words and inv_words:
                word_overlap = len(txn_words & inv_words) / max(len(txn_words), len(inv_words))
                ratio = max(ratio, word_overlap)

            vendor_score = ratio
            vendor_match = ratio > 0.75
            if vendor_match:
                reasons.append(f"Vendor match ({ratio:.0%}): '{transaction.counterparty_name}' ↔ '{invoice.vendor_name}'")

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

    # --- Reference / Verwendungszweck (10%) ---
    ref_score = 0.0
    ref_match = False

    # Check if invoice number appears in transaction reference
    if transaction.reference and invoice.invoice_number:
        if invoice.invoice_number.lower() in transaction.reference.lower():
            ref_score, ref_match = 1.0, True
            reasons.append(f"Invoice number '{invoice.invoice_number}' found in reference")

    # Check payment reference match
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
        if "High confidence" not in str(reasons):
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
