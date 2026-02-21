import pytest
import aiosqlite
import json
import uuid
import datetime
from backend.database import DB_PATH
from backend.agent import chat_with_agent

@pytest.fixture
async def seed_german_vat_data():
    """
    Seeds a dummy set of resolved transactions and invoices for January 2026.
    Returns:
        dict: The dummy company created.
    """
    company_id = str(uuid.uuid4())
    
    # 1. Create a dummy company
    company_profile = {
        "name": "Acme GmbH",
        "jurisdictions": ["DE"],
        "industry": "Software",
        "entity_type": "GmbH",
        "vat_number": "DE987654321"
    }
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO companies (id, name, profile)
            VALUES (?, ?, ?)
        """, (company_id, "Acme GmbH", json.dumps(company_profile)))
        
        # 2. Insert dummy transactions for Jan 2026
        # To make it simple:
        # Total Revenue (Incoming) = €50,000 (19% VAT = €9,500)
        # Total Expenses (Outgoing) = €20,000 (19% VAT = €3,800)
        # Expected Net VAT Payable = €5,700
        
        # Revenue
        await db.execute("""
            INSERT INTO transactions (id, company_id, date, description, amount, currency, account, status, jurisdiction, match_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), company_id, "2026-01-10", "Client Software License", 50000.00, "EUR", "DE Main", "matched", "DE", str(uuid.uuid4())))
        
        # Expenses
        await db.execute("""
            INSERT INTO transactions (id, company_id, date, description, amount, currency, account, status, jurisdiction, match_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), company_id, "2026-01-15", "Server Hosting", -20000.00, "EUR", "DE Main", "matched", "DE", str(uuid.uuid4())))
        
        # 3. Create pre-aggregated financial summary which `run_analysis` or `get_period_financials` might use
        jan_summary = {
            "period": "2026-01",
            "jurisdiction": "DE",
            "metrics": {
                "total_revenue": 50000.00,
                "total_expenses": 20000.00,
                "output_vat": 9500.00,
                "input_vat": 3800.00,
                "net_payable": 5700.00
            }
        }
        await db.execute("""
            INSERT INTO financial_summaries (id, company_id, jurisdiction, period, data)
            VALUES (?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), company_id, "DE", "2026-01", json.dumps(jan_summary)))
        
        await db.commit()
    
    yield {"company_id": company_id, "name": "Acme GmbH"}
    
    # Cleanup after test
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM companies WHERE id = ?", (company_id,))
        await db.execute("DELETE FROM transactions WHERE company_id = ?", (company_id,))
        await db.execute("DELETE FROM financial_summaries WHERE company_id = ?", (company_id,))
        await db.commit()

@pytest.mark.asyncio
async def test_agentic_vat_return_generation(seed_german_vat_data):
    """
    Test that the agent can calculate the German VAT return using the sandbox executor.
    """
    company_id = seed_german_vat_data["company_id"]
    
    # Send a prompt intentionally requiring computation reading from the DB
    prompt = (
        "Calculate the net German VAT payable for January 2026 for my company. "
        "Look into the transactions or my period financials for DE for Jan 2026. "
        "The VAT rate in Germany is 19% on revenue and you can claim 19% back on expenses. "
        "Compute the Output VAT, Input VAT, and the Net VAT Payable. Be concise."
    )
    
    response = await chat_with_agent(company_id=company_id, message=prompt)
    
    print(f"\n[Agent Response]\n{response}\n")
    
    # The agent should invoke run_analysis or get_period_financials, get the values (50000 and 20000), 
    # compute 19% on both, and arrive at 5700.
    
    assert "9,500" in response or "9500" in response, "Agent failed to calculate Output VAT"
    assert "3,800" in response or "3800" in response, "Agent failed to calculate Input VAT"
    assert "5,700" in response or "5700" in response, "Agent failed to calculate Net VAT payable"
