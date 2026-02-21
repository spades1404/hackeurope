import asyncio
import json
import uuid
from datetime import datetime
import os
import aiosqlite
from dotenv import load_dotenv

from backend.database import DB_PATH, init_db
from backend.agent import chat_with_agent, execute_run_analysis, execute_generate_compliance_document
from backend.pdf_export import render_document_to_pdf

load_dotenv()

async def generate_dummy_data():
    """Seeds the DB with dummy data for a German VAT return test."""
    company_id = str(uuid.uuid4())
    action_id = str(uuid.uuid4())
    
    company_profile = {
        "name": "Acme GmbH TEST",
        "jurisdictions": ["DE"],
        "industry": "Software",
        "entity_type": "GmbH",
        "vat_number": "DE987654321",
        "employee_count": 10
    }
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Create company
        await db.execute("""
            INSERT INTO companies (id, name, profile)
            VALUES (?, ?, ?)
        """, (company_id, "Acme GmbH TEST", json.dumps(company_profile)))
        
        # Create action (VAT Return)
        action_data = {
            "form": "Umsatzsteuer-Voranmeldung",
            "output_type": "vat_return",
            "tax_rate": 0.19
        }
        await db.execute(
            """INSERT INTO actions (id, company_id, obligation_id, obligation_name, jurisdiction, deadline, prep_start_date, status, priority, action_data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (action_id, company_id, "vat_de", "Monthly VAT Return", "DE", "2026-02-10", "2026-02-01", "in_progress", "high", json.dumps(action_data))
        )
        
        # Insert some transactions for Jan 2026
        transactions = [
            (str(uuid.uuid4()), company_id, "DE", "revenue", "sales", "Client Project DE", 50000.0, "EUR", "2026-01-10", "2026-Q1", True, "{}"),
            (str(uuid.uuid4()), company_id, "DE", "expense", "software", "Server Hosting", -20000.0, "EUR", "2026-01-15", "2026-Q1", True, "{}")
        ]
        await db.executemany(
            """INSERT INTO transactions (id, company_id, jurisdiction, transaction_type, category, description, amount, currency, transaction_date, quarter, tax_relevant, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            transactions
        )
        
        # Insert financial summary (agent might use this instead of transactions)
        summary_data = {
            "total_revenue": 50000.0,
            "total_expenses": 20000.0,
            "annual_revenue": 50000.0, # required by doc generator
            "output_vat": 9500.0,
            "input_vat": 3800.0,
            "net_payable": 5700.0
        }
        await db.execute("""
            INSERT INTO financial_summaries (id, company_id, jurisdiction, period, period_type, summary)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), company_id, "DE", "2026-Q1", "quarterly", json.dumps(summary_data)))
        
        await db.commit()
        
    return company_id, action_id

async def run_test():
    print("Initializing Database...")
    await init_db()
    
    print("Seeding dummy data for German VAT...")
    company_id, action_id = await generate_dummy_data()
    print(f"Created Company: {company_id} | Action: {action_id}")
    
    print("--- 2. Testing Agentic Document Generation ---")
    doc_result = await execute_generate_compliance_document(company_id, action_id)
    print(f"Document Tool Result: {doc_result}\n")
    
    
    if not os.getenv("GEMINI_API_KEY"):
        print("WARNING: GEMINI_API_KEY environment variable is missing. The test might fail.")
        return
    
    # Check if a document was created and linked to the action
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM actions WHERE id = ?", (action_id,)) as cursor:
            action_row = await cursor.fetchone()
            
        if not action_row or not action_row['document_id']:
            print("ERROR: Agent did not link a document to the action.")
            return
            
        doc_id = action_row['document_id']
        async with db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)) as cursor:
            doc_row = await cursor.fetchone()
            
        if not doc_row:
            print(f"ERROR: Document {doc_id} not found in database.")
            return
            
        doc_content = json.loads(doc_row['content'])
        print(f"SUCCESS: Found generated document: {doc_content.get('title')} ({doc_id})")
        
        # Render to PDF
        pdf_bytes = render_document_to_pdf(doc_content, "Acme GmbH TEST")
        pdf_path = os.path.join(os.path.dirname(__file__), "..", "test_vat_return.pdf")
        
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
            
        print(f"SUCCESS: PDF exported successfully to: {pdf_path}")
        
    
if __name__ == "__main__":
    asyncio.run(run_test())
