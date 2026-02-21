"""Test the matching engine using the OCR output from the last extraction run."""

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from schemas import ExtractedInvoiceData, Transaction
from matching_engine import score_match

# --- Transaction (row 3 from CSV: Grafton Group plc) ---
transaction = Transaction(
    id="IE-TXN-GRAFTON-001",
    date=date(2023, 1, 3),
    amount=-48950.29,
    currency="EUR",
    counterparty_name="Grafton Group plc",
    counterparty_iban="IE29PTSB99061710234567",
    reference=None,
)

# --- Extracted invoice data (from last OCR run) ---
extracted = ExtractedInvoiceData(
    invoice_number="IE-202301-71023",
    invoice_date=date(2023, 1, 3),
    due_date=date(2023, 2, 2),
    vendor_name="GRAFTON GROUP PLC",
    vendor_address=None,
    vendor_tax_id=None,
    vendor_iban="IE29PTSB99061710234567",
    buyer_name="Tuna Tax Ltd.",
    net_amount=43128.01,
    vat_rate=13.5,
    vat_amount=5822.28,
    gross_amount=48950.29,
    line_items=[{"description": "Monthly retainer invoice", "quantity": 1, "unit_price": 43128.01, "total": 43128.01}],
    payment_reference=None,
)

# --- Run matching engine ---
proposal = score_match(transaction, extracted)

print("=== Transaction ===")
print(f"  Counterparty: {transaction.counterparty_name}")
print(f"  Date:         {transaction.date}")
print(f"  Amount:       {transaction.currency} {abs(transaction.amount):,.2f}")
print(f"  IBAN:         {transaction.counterparty_iban}")

print("\n=== Extracted Invoice ===")
print(f"  Vendor:       {extracted.vendor_name}")
print(f"  Invoice No.:  {extracted.invoice_number}")
print(f"  Date:         {extracted.invoice_date}")
print(f"  Gross:        EUR {extracted.gross_amount:,.2f}")
print(f"  IBAN:         {extracted.vendor_iban}")

print("\n=== Match Result ===")
print(f"  Status:       {proposal.status.value.upper()}")
print(f"  Confidence:   {proposal.confidence_score:.1%}")
print(f"\n  Signal breakdown:")
print(f"    Amount match:    {proposal.amount_match}")
print(f"    Vendor match:    {proposal.vendor_match}")
print(f"    Date match:      {proposal.date_match}")
print(f"    Reference match: {proposal.reference_match}")
print(f"    IBAN match:      {proposal.iban_match}")
print(f"\n  Reasons:")
for r in proposal.match_reasons:
    print(f"    - {r}")
