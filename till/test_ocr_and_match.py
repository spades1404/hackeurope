"""Run OCR on the latest Gmail PDF, then score it against its transaction."""

import json
import sys
import csv
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from gmail_service import GmailService
from invoice_extractor import extract_invoice_data
from matching_engine import score_match
from schemas import Transaction

CSV_PATH = Path(__file__).parent / "test_data" / "transactions.csv"


def find_transaction_for_email(counterparty_name: str) -> Transaction | None:
    """Look up the first matching transaction row from the CSV."""
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if counterparty_name.lower() in row["Counterparty Name"].lower():
                return Transaction(
                    id=row["Transaction ID"],
                    date=date.fromisoformat(row["Transaction Date (Local)"]),
                    amount=-float(row["Total Amount (incl. VAT)"]),
                    currency=row["Currency"] or "EUR",
                    counterparty_name=row["Counterparty Name"],
                    counterparty_iban=row["Counterparty IBAN"] or None,
                    reference=row["Reference"] or None,
                )
    return None


def main():
    # --- Step 1: fetch latest email with PDF ---
    print("Authenticating with Gmail...")
    gmail = GmailService()
    gmail.authenticate()

    print("Fetching latest email with PDF attachment...")
    messages = gmail.search_emails("has:attachment filename:pdf", max_results=1)
    if not messages:
        print("No emails with PDF found.")
        return

    candidate = gmail.get_email_metadata(messages[0]["id"])
    if not candidate or not candidate.has_pdf:
        print("No PDF in latest email.")
        return

    print(f"\n=== Email ===")
    print(f"  From:    {candidate.email_from}")
    print(f"  Subject: {candidate.email_subject}")
    print(f"  Date:    {candidate.email_date}")
    print(f"  PDF:     {candidate.pdf_filename}")

    # --- Step 2: download PDF and run OCR ---
    print("\nDownloading PDF and running OCR...")
    email_invoice = gmail.download_pdf_for_candidate(candidate)
    extracted = extract_invoice_data(email_invoice.pdf_base64)

    print("\n=== Extracted Invoice (raw JSON) ===")
    print(json.dumps(extracted.model_dump(), indent=2, default=str))

    # --- Step 3: find matching transaction from CSV ---
    vendor = extracted.vendor_name or ""
    transaction = find_transaction_for_email(vendor)

    if not transaction:
        print(f"\nNo transaction found in CSV matching vendor '{vendor}'")
        return

    print(f"\n=== Matched Transaction from CSV ===")
    print(f"  ID:           {transaction.id}")
    print(f"  Counterparty: {transaction.counterparty_name}")
    print(f"  Date:         {transaction.date}")
    print(f"  Amount:       {transaction.currency} {abs(transaction.amount):,.2f}")
    print(f"  IBAN:         {transaction.counterparty_iban}")
    print(f"  Reference:    {transaction.reference}")

    # --- Step 4: run matching engine ---
    proposal = score_match(transaction, extracted)

    print(f"\n=== Match Result ===")
    print(f"  Status:     {proposal.status.value.upper()}")
    print(f"  Confidence: {proposal.confidence_score:.1%}")
    print(f"\n  Signals:")
    print(f"    Amount:    {proposal.amount_match}")
    print(f"    Vendor:    {proposal.vendor_match}")
    print(f"    Date:      {proposal.date_match}")
    print(f"    Reference: {proposal.reference_match}")
    print(f"    IBAN:      {proposal.iban_match}")
    print(f"\n  Reasons:")
    for r in proposal.match_reasons:
        print(f"    - {r}")


if __name__ == "__main__":
    main()
