"""
Demo Seed Script

Creates:
1. A company: "Tuna Tax Ltd" operating in UK, DE, US, AU
2. Two users: worker@tunatax.com (worker) and business@tunatax.com (business)
3. ~40 pre-reconciled bank transactions + matching invoices (historical data)
4. ~15 compliance actions across jurisdictions (some overdue, some upcoming, one due TOMORROW)
5. A few match proposals in various states

Run automatically on first startup if DB is empty, or manually via API.
"""

import uuid
from datetime import date, timedelta, datetime
from hashlib import sha256
import json
import bcrypt

async def seed_demo_data(db):
    """Main seed function. Call from server startup."""

    # Check if already seeded
    companies = await db.list_companies()
    if companies:
        return False  # Already seeded

    company_id = "tuna-tax-ltd"
    today = date.today()  # Should be ~Feb 22, 2026 for the demo

    # ── 1. Create Company ──────────────────────────────
    company_profile = {
        "company_name": "Tuna Tax Ltd",
        "jurisdictions": ["UK", "DE", "US", "AU"],
        "entity_types": {
            "UK": ["ltd"],
            "DE": ["gmbh"],
            "US": ["c_corp"],
            "AU": ["pty_ltd"],
        },
        "fiscal_year_end": {"UK": 3, "DE": 12, "US": 12, "AU": 6},
        "employees": {"UK": 25, "DE": 15, "US": 30, "AU": 8},
        "annual_revenue": {"UK": 2400000, "DE": 1800000, "US": 4200000, "AU": 950000},
        "registered_address": "14 Finsbury Square, London EC2A 1BR",
        "tax_ids": {
            "UK": "GB 123 4567 89",
            "DE": "DE 312 456 789",
            "US": "87-1234567",
            "AU": "12 345 678 901",
        },
    }
    await db.create_company(company_id, "user-business-1", "Tuna Tax Ltd", company_profile)

    # ── 2. Create Users ────────────────────────────────
    worker_pw = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()
    business_pw = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()

    await db.create_user("user-worker-1", "worker@tunatax.com", "Sarah Chen", "worker")
    await db.create_user("user-business-1", "business@tunatax.com", "James Morton", "business")

    # ── 3. Historical Reconciled Transactions + Invoices ───
    historical_pairs = [
        # UK transactions (GBP)
        {"txn_id": "TXN-20251201-001", "inv_id": "INV-UK-2025-1001", "vendor": "Crown Digital Ltd", "amount": 8750.00, "currency": "GBP", "date": "2025-12-05", "jurisdiction": "UK", "category": "expense", "desc": "Marketing retainer December", "vat_rate": 20.0, "vat": 1458.33, "net": 7291.67, "ref": "CD-DEC-2025"},
        {"txn_id": "TXN-20251215-002", "inv_id": "INV-UK-2025-1002", "vendor": "Manchester Hosting Co", "amount": 3200.00, "currency": "GBP", "date": "2025-12-15", "jurisdiction": "UK", "category": "expense", "desc": "Server hosting Q4", "vat_rate": 20.0, "vat": 533.33, "net": 2666.67, "ref": "MH-Q4-25"},
        {"txn_id": "TXN-20260105-003", "inv_id": "INV-UK-2026-1003", "vendor": "Barclays Payroll Services", "amount": 45000.00, "currency": "GBP", "date": "2026-01-05", "jurisdiction": "UK", "category": "payroll", "desc": "January payroll - 25 staff", "vat_rate": 0, "vat": 0, "net": 45000.00, "ref": "PAY-JAN-26"},
        {"txn_id": "TXN-20260110-004", "inv_id": "INV-UK-2026-1004", "vendor": "WeWork London", "amount": 6800.00, "currency": "GBP", "date": "2026-01-10", "jurisdiction": "UK", "category": "expense", "desc": "Office rent January", "vat_rate": 20.0, "vat": 1133.33, "net": 5666.67, "ref": "WW-JAN-26"},
        {"txn_id": "TXN-20260120-005", "inv_id": None, "vendor": None, "amount": 185000.00, "currency": "GBP", "date": "2026-01-20", "jurisdiction": "UK", "category": "revenue", "desc": "Client payment - Acme Corp", "vat_rate": 20.0, "vat": 30833.33, "net": 154166.67, "ref": "ACME-Q4-25"},
        {"txn_id": "TXN-20260201-006", "inv_id": "INV-UK-2026-1005", "vendor": "Crown Digital Ltd", "amount": 8750.00, "currency": "GBP", "date": (today - timedelta(days=1)).isoformat(), "jurisdiction": "UK", "category": "expense", "desc": "Marketing retainer February", "vat_rate": 20.0, "vat": 1458.33, "net": 7291.67, "ref": "CD-FEB-2026"},
        {"txn_id": "TXN-20260205-007", "inv_id": "INV-UK-2026-1006", "vendor": "Barclays Payroll Services", "amount": 45000.00, "currency": "GBP", "date": (today - timedelta(days=2)).isoformat(), "jurisdiction": "UK", "category": "payroll", "desc": "February payroll - 25 staff", "vat_rate": 0, "vat": 0, "net": 45000.00, "ref": "PAY-FEB-26"},

        # DE transactions (EUR)
        {"txn_id": "TXN-20251210-010", "inv_id": "INV-DE-2025-2001", "vendor": "Müller Maschinenbau GmbH", "amount": 14280.00, "currency": "EUR", "date": "2025-12-10", "jurisdiction": "DE", "category": "expense", "desc": "Machine parts Q4 order", "vat_rate": 19.0, "vat": 2281.01, "net": 11998.99, "ref": "MM-Q4-2025"},
        {"txn_id": "TXN-20260108-011", "inv_id": "INV-DE-2026-2002", "vendor": "Berlin Bürobedarf AG", "amount": 1890.00, "currency": "EUR", "date": (today - timedelta(days=3)).isoformat(), "jurisdiction": "DE", "category": "expense", "desc": "Office supplies January", "vat_rate": 19.0, "vat": 301.76, "net": 1588.24, "ref": "BB-JAN-26"},
        {"txn_id": "TXN-20260115-012", "inv_id": "INV-DE-2026-2003", "vendor": "SAP Deutschland SE", "amount": 22500.00, "currency": "EUR", "date": (today - timedelta(days=1)).isoformat(), "jurisdiction": "DE", "category": "expense", "desc": "ERP license annual", "vat_rate": 19.0, "vat": 3592.44, "net": 18907.56, "ref": "SAP-2026"},
        {"txn_id": "TXN-20260120-013", "inv_id": None, "vendor": None, "amount": 145000.00, "currency": "EUR", "date": "2026-01-20", "jurisdiction": "DE", "category": "revenue", "desc": "Client payment - Deutsche Telekom project", "vat_rate": 19.0, "vat": 23151.26, "net": 121848.74, "ref": "DT-Q4-25"},

        # US transactions (USD)
        {"txn_id": "TXN-20251220-020", "inv_id": "INV-US-2025-3001", "vendor": "Apex Cloud Services Inc", "amount": 22100.00, "currency": "USD", "date": "2025-12-20", "jurisdiction": "US", "category": "expense", "desc": "Cloud infrastructure December", "vat_rate": 0, "vat": 0, "net": 22100.00, "ref": "APEX-DEC-25"},
        {"txn_id": "TXN-20260102-021", "inv_id": "INV-US-2026-3002", "vendor": "ADP Payroll", "amount": 68000.00, "currency": "USD", "date": (today - timedelta(days=4)).isoformat(), "jurisdiction": "US", "category": "payroll", "desc": "January payroll - 30 staff", "vat_rate": 0, "vat": 0, "net": 68000.00, "ref": "ADP-JAN-26"},
        {"txn_id": "TXN-20260115-022", "inv_id": "INV-US-2026-3003", "vendor": "Salesforce Inc", "amount": 4800.00, "currency": "USD", "date": (today - timedelta(days=2)).isoformat(), "jurisdiction": "US", "category": "expense", "desc": "CRM license Q1", "vat_rate": 0, "vat": 0, "net": 4800.00, "ref": "SF-Q1-26"},
        {"txn_id": "TXN-20260125-023", "inv_id": None, "vendor": None, "amount": 320000.00, "currency": "USD", "date": "2026-01-25", "jurisdiction": "US", "category": "revenue", "desc": "Client payment - Fortune 500 consulting", "vat_rate": 0, "vat": 0, "net": 320000.00, "ref": "F500-Q4-25"},

        # AU transactions (AUD)
        {"txn_id": "TXN-20260110-030", "inv_id": "INV-AU-2026-4001", "vendor": "Sydney Logistics Pty", "amount": 3420.50, "currency": "AUD", "date": "2026-01-10", "jurisdiction": "AU", "category": "expense", "desc": "Shipping Jan batch", "vat_rate": 10.0, "vat": 311.14, "net": 3109.36, "ref": "SL-JAN-26"},
        {"txn_id": "TXN-20260120-031", "inv_id": None, "vendor": None, "amount": 87500.00, "currency": "AUD", "date": "2026-01-20", "jurisdiction": "AU", "category": "revenue", "desc": "Client payment - Telstra project", "vat_rate": 10.0, "vat": 7954.55, "net": 79545.45, "ref": "TEL-Q4-25"},
    ]

    for pair in historical_pairs:
        # Create bank transaction
        await db.create_bank_transaction(
            id=pair["txn_id"],
            company_id=company_id,
            description=pair["desc"],
            amount=-pair["amount"] if pair["category"] != "revenue" else pair["amount"],
            currency=pair["currency"],
            transaction_date=pair["date"],
            account_name=f"{pair['jurisdiction']} Business Account",
            jurisdiction=pair["jurisdiction"],
            category=pair["category"],
            counterparty_name=pair.get("vendor") or "Client",
            payment_reference=pair["ref"],
            reconciliation_status="approved",
            matched_invoice_id=pair.get("inv_id"),
        )

        # Create matching invoice (if it has one — revenue items don't have vendor invoices)
        if pair.get("inv_id"):
            await db.create_invoice(
                id=pair["inv_id"],
                company_id=company_id,
                invoice_number=pair["ref"],
                invoice_date=pair["date"],
                vendor_name=pair["vendor"],
                net_amount=pair["net"],
                vat_rate=pair["vat_rate"],
                vat_amount=pair["vat"],
                gross_amount=pair["amount"],
                currency=pair["currency"],
                payment_reference=pair["ref"],
                jurisdiction=pair["jurisdiction"],
                reconciliation_status="approved",
                matched_transaction_id=pair["txn_id"],
            )

    # ── 4. Compliance Actions ──────────────────────────
    tomorrow = today + timedelta(days=1)
    actions = [
        {
            "id": "action-uk-vat-q4-2025",
            "company_id": company_id,
            "obligation_id": "UK-VAT",
            "obligation_name": "UK VAT Return (Q4 2025)",
            "jurisdiction": "UK",
            "form": "VAT100",
            "deadline": tomorrow.isoformat(),
            "period_start": "2025-10-01",
            "period_end": "2025-12-31",
            "status": "pending_review",
            "priority": "critical",
            "output_type": "vat_return",
        },
        {
            "id": "action-uk-ct-2025",
            "company_id": company_id,
            "obligation_id": "UK-CT",
            "obligation_name": "UK Corporation Tax (FY 2025)",
            "jurisdiction": "UK",
            "form": "CT600",
            "deadline": (today + timedelta(days=270)).isoformat(),
            "period_start": "2025-04-01",
            "period_end": "2026-03-31",
            "status": "upcoming",
            "priority": "low",
            "output_type": "tax_return",
        },
        {
            "id": "action-uk-paye-feb",
            "company_id": company_id,
            "obligation_id": "UK-PAYE",
            "obligation_name": "UK PAYE RTI (February 2026)",
            "jurisdiction": "UK",
            "form": "FPS",
            "deadline": (today + timedelta(days=6)).isoformat(),
            "period_start": "2026-02-01",
            "period_end": "2026-02-28",
            "status": "upcoming",
            "priority": "high",
            "output_type": "payroll_submission",
        },
        {
            "id": "action-de-vat-jan",
            "company_id": company_id,
            "obligation_id": "DE-VAT",
            "obligation_name": "DE Umsatzsteuer (January 2026)",
            "jurisdiction": "DE",
            "form": "UStVA",
            "deadline": (today + timedelta(days=18)).isoformat(),
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "status": "upcoming",
            "priority": "high",
            "output_type": "vat_return",
        },
        {
            "id": "action-de-cit-2025",
            "company_id": company_id,
            "obligation_id": "DE-CIT",
            "obligation_name": "DE Körperschaftsteuer (FY 2025)",
            "jurisdiction": "DE",
            "form": "KSt 1",
            "deadline": (today + timedelta(days=159)).isoformat(),
            "period_start": "2025-01-01",
            "period_end": "2025-12-31",
            "status": "upcoming",
            "priority": "medium",
            "output_type": "tax_return",
        },
        {
            "id": "action-us-est-q1",
            "company_id": company_id,
            "obligation_id": "US-EST",
            "obligation_name": "US Estimated Tax (Q1 2026)",
            "jurisdiction": "US",
            "form": "Form 1120-W",
            "deadline": "2026-04-15",
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
            "status": "upcoming",
            "priority": "medium",
            "output_type": "payment_voucher",
        },
        {
            "id": "action-us-payroll-q1",
            "company_id": company_id,
            "obligation_id": "US-PAYROLL",
            "obligation_name": "US Payroll Tax Return (Q1 2026)",
            "jurisdiction": "US",
            "form": "Form 941",
            "deadline": "2026-04-30",
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
            "status": "upcoming",
            "priority": "medium",
            "output_type": "payroll_return",
        },
        {
            "id": "action-au-bas-q2",
            "company_id": company_id,
            "obligation_id": "AU-BAS",
            "obligation_name": "AU Business Activity Statement (Q2 FY26)",
            "jurisdiction": "AU",
            "form": "BAS",
            "deadline": "2026-02-28",
            "period_start": "2025-10-01",
            "period_end": "2025-12-31",
            "status": "upcoming",
            "priority": "high",
            "output_type": "activity_statement",
        },
        {
            "id": "action-uk-vat-q3-2025",
            "company_id": company_id,
            "obligation_id": "UK-VAT",
            "obligation_name": "UK VAT Return (Q3 2025)",
            "jurisdiction": "UK",
            "form": "VAT100",
            "deadline": "2025-11-07",
            "period_start": "2025-07-01",
            "period_end": "2025-09-30",
            "status": "submitted",
            "priority": "low",
            "output_type": "vat_return",
        },
    ]

    for action in actions:
        await db.create_action(**action)

    # ── 5. Generate Initial Match Proposals for Dashboard ──
    from backend.demo_generator import generate_fresh_demo_data
    # Generate 2 batches to ensure there's plenty of test data for approvals
    await generate_fresh_demo_data(db, company_id)
    await generate_fresh_demo_data(db, company_id)

    return True
