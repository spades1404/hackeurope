"""
Generates fresh demo data that simulates:
- New bank transactions appearing from Open Banking
- New invoices arriving from Gmail
- The till linking engine running and producing match proposals

Each call generates 5-8 new transaction/invoice pairs in various states.
"""

import random
from datetime import date, timedelta
import uuid

DEMO_VENDORS = [
    {"name": "HubSpot Ireland Ltd", "jurisdiction": "UK", "currency": "GBP", "tax_id": "IE9803175K"},
    {"name": "AWS Europe", "jurisdiction": "DE", "currency": "EUR", "tax_id": "LU26888023"},
    {"name": "Notion Labs Inc", "jurisdiction": "US", "currency": "USD", "tax_id": None},
    {"name": "Canva Pty Ltd", "jurisdiction": "AU", "currency": "AUD", "tax_id": "ABN 80 158 929 938"},
    {"name": "Stripe Payments UK", "jurisdiction": "UK", "currency": "GBP", "tax_id": "GB 184 8813 85"},
    {"name": "Google Cloud EMEA", "jurisdiction": "DE", "currency": "EUR", "tax_id": "IE6388047V"},
    {"name": "Slack Technologies", "jurisdiction": "US", "currency": "USD", "tax_id": None},
    {"name": "Atlassian Pty Ltd", "jurisdiction": "AU", "currency": "AUD", "tax_id": "ABN 53 168 427 318"},
    {"name": "Figma Inc", "jurisdiction": "US", "currency": "USD", "tax_id": None},
    {"name": "Intercom R&D", "jurisdiction": "UK", "currency": "GBP", "tax_id": "IE9753535I"},
]

VAT_RATES = {"UK": 20.0, "DE": 19.0, "AU": 10.0, "US": 0.0}

async def generate_fresh_demo_data(db, company_id: str) -> dict:
    """
    Generate 5-8 new transactions with matching invoices and match proposals.
    
    Returns summary of what was created.
    """
    today = date.today()
    batch_size = random.randint(5, 8)
    created = {"transactions": 0, "invoices": 0, "match_proposals": 0}

    for i in range(batch_size):
        vendor = random.choice(DEMO_VENDORS)
        net_amount = round(random.uniform(500, 25000), 2)
        vat_rate = VAT_RATES.get(vendor["jurisdiction"], 0)
        vat_amount = round(net_amount * vat_rate / 100, 2)
        gross_amount = round(net_amount + vat_amount, 2)
        txn_date = today - timedelta(days=random.randint(0, 5))
        inv_date = txn_date - timedelta(days=random.randint(0, 3))
        ref = f"{vendor['name'][:3].upper()}-{today.strftime('%Y%m')}-{random.randint(1000,9999)}"

        txn_id = f"TXN-{today.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
        inv_id = f"INV-{vendor['jurisdiction']}-{today.strftime('%Y')}-{random.randint(10000,99999)}"

        # Decide match quality (what the till engine would produce)
        scenario = random.choices(
            ["perfect_match", "needs_review", "low_confidence"],
            weights=[0.5, 0.35, 0.15],
        )[0]

        # Create the bank transaction
        txn_amount = -gross_amount  # Outgoing payment
        if scenario == "needs_review":
            # Slight amount discrepancy
            txn_amount = -(gross_amount + round(random.uniform(-50, 50), 2))
        elif scenario == "low_confidence":
            # Large amount discrepancy
            txn_amount = -(gross_amount + round(random.uniform(200, 1000), 2))

        await db.create_bank_transaction(
            id=txn_id,
            company_id=company_id,
            description=f"Payment to {vendor['name']} - {ref}",
            amount=txn_amount,
            currency=vendor["currency"],
            transaction_date=txn_date.isoformat(),
            account_name=f"{vendor['jurisdiction']} Business Account",
            jurisdiction=vendor["jurisdiction"],
            category="expense",
            counterparty_name=vendor["name"],
            payment_reference=ref,
            reconciliation_status="unreconciled",
        )
        created["transactions"] += 1

        # Create matching invoice
        await db.create_invoice(
            id=inv_id,
            company_id=company_id,
            invoice_number=ref,
            invoice_date=inv_date.isoformat(),
            due_date=(inv_date + timedelta(days=30)).isoformat(),
            vendor_name=vendor["name"],
            vendor_tax_id=vendor.get("tax_id"),
            net_amount=net_amount,
            vat_rate=vat_rate,
            vat_amount=vat_amount,
            gross_amount=gross_amount,
            currency=vendor["currency"],
            payment_reference=ref,
            jurisdiction=vendor["jurisdiction"],
            source_email_from=f"billing@{vendor['name'].lower().replace(' ', '').replace('.','')}.com",
            source_email_subject=f"Invoice {ref} from {vendor['name']}",
            source_email_date=inv_date.isoformat(),
            reconciliation_status="unreconciled",
        )
        created["invoices"] += 1

        # Create match proposal (simulating the till engine output)
        confidence = 0.985 if scenario == "perfect_match" else round(random.uniform(0.55, 0.82), 3)
        amount_match = scenario == "perfect_match"

        proposal_status = "matched" if scenario == "perfect_match" else "needs_review"
        proposal = {
            "id": f"mp-{txn_id}",
            "transaction_id": txn_id,
            "invoice_id": inv_id,
            "confidence_score": confidence,
            "status": proposal_status,
            "amount_match": amount_match,
            "date_match": True,
            "vendor_match": True,
            "reference_match": scenario == "perfect_match",
            "iban_match": False,
            "match_reasons": [],
        }

        reasons = []
        if amount_match:
            reasons.append(f"Amount matches: {vendor['currency']} {gross_amount:,.2f}")
        else:
            reasons.append(f"Amount close but not exact: invoice {gross_amount:,.2f} vs transaction {abs(txn_amount):,.2f}")
        reasons.append(f"Vendor name matches: {vendor['name']}")
        reasons.append(f"Invoice date within {abs((txn_date - inv_date).days)} days of transaction")
        if scenario == "perfect_match":
            reasons.append(f"Payment reference {ref} found in invoice")
        proposal["match_reasons"] = reasons

        await db.create_match_proposal(**proposal)
        created["match_proposals"] += 1

    return created
