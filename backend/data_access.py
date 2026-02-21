"""
Data access functions exposed to the Gemini agent via function calling.
Each function queries SQLite and returns structured data the agent
can use to answer questions or generate documents.
"""
import aiosqlite
import json
from datetime import datetime
from backend.database import DB_PATH
from backend.compliance_engine import load_knowledge_base

async def get_financial_summary(
    company_id: str,
    jurisdiction: str,
    period: str
) -> dict:
    """Get the aggregated financial summary for a company in a specific
    jurisdiction and period.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT summary FROM financial_summaries WHERE company_id = ? AND jurisdiction = ? AND period = ?",
            (company_id, jurisdiction, period)
        ) as cur:
            row = await cur.fetchone()
            if row:
                return json.loads(row['summary'])

        # If not found, compute on the fly using transactions
        # Simple quarter parsing logic (assumes period matches the 'quarter' field or we do an annual roll up)
        query = "SELECT transaction_type, category, SUM(amount) as total FROM transactions WHERE company_id = ? AND jurisdiction = ?"
        params = [company_id, jurisdiction]
        
        if "-Q" in period:
            query += " AND quarter = ?"
            params.append(period)
        elif "-annual" in period:
            year = period.split("-")[0]
            query += " AND quarter LIKE ?"
            params.append(f"{year}-%")
            
        query += " GROUP BY transaction_type, category"
        
        summary = {
            "gross_revenue": 0,
            "cost_of_goods_sold": 0,
            "operating_expenses": 0,
            "total_wages": 0,
            "output_vat": 0,
            "input_vat": 0,
            "tax_payments": 0,
            "currency": "USD" # default
        }
        
        async with db.execute("SELECT currency FROM transactions WHERE company_id = ? AND jurisdiction = ? LIMIT 1", (company_id, jurisdiction)) as cur:
            c_row = await cur.fetchone()
            if c_row:
                summary["currency"] = c_row["currency"]

        async with db.execute(query, tuple(params)) as cur:
            rows = await cur.fetchall()
            for r in rows:
                ttype = r['transaction_type']
                cat = r['category']
                amt = r['total']
                
                if ttype == 'revenue':
                    summary["gross_revenue"] += amt
                elif ttype == 'expense':
                    if cat == 'cost_of_goods_sold':
                        summary["cost_of_goods_sold"] += amt
                    else:
                        summary["operating_expenses"] += amt
                elif ttype == 'payroll':
                    summary["total_wages"] += amt
                elif ttype == 'vat_collected':
                    summary["output_vat"] += amt
                elif ttype == 'vat_paid':
                    summary["input_vat"] += amt
                elif ttype == 'tax_payment':
                    summary["tax_payments"] += amt
                    
        return summary

async def get_transactions(
    company_id: str,
    jurisdiction: str = None,
    transaction_type: str = None,
    date_from: str = None,
    date_to: str = None,
    min_amount: float = None,
    max_amount: float = None,
    category: str = None,
    limit: int = 100
) -> list[dict]:
    """Query transactions with flexible filters."""
    query = "SELECT * FROM transactions WHERE company_id = ?"
    params = [company_id]
    
    if jurisdiction:
        query += " AND jurisdiction = ?"
        params.append(jurisdiction)
    if transaction_type:
        query += " AND transaction_type = ?"
        params.append(transaction_type)
    if date_from:
        query += " AND transaction_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND transaction_date <= ?"
        params.append(date_to)
    if min_amount is not None:
        query += " AND amount >= ?"
        params.append(min_amount)
    if max_amount is not None:
        query += " AND amount <= ?"
        params.append(max_amount)
    if category:
        query += " AND category = ?"
        params.append(category)
        
    query += f" ORDER BY transaction_date DESC LIMIT {limit}"
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, tuple(params)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

async def get_transaction_aggregates(
    company_id: str,
    jurisdiction: str,
    period: str,
    group_by: str = "transaction_type"
) -> dict:
    """Get aggregated transaction totals grouped by a field."""
    # Build safely
    allowed_groups = ["transaction_type", "category", "quarter"]
    if group_by not in allowed_groups:
        group_by = "transaction_type"
        
    query = f"SELECT {group_by}, SUM(amount) as total FROM transactions WHERE company_id = ? AND jurisdiction = ?"
    params = [company_id, jurisdiction]
    
    if "-Q" in period:
        query += " AND quarter = ?"
        params.append(period)
    elif "-annual" in period:
        year = period.split("-")[0]
        query += " AND quarter LIKE ?"
        params.append(f"{year}-%")
        
    query += f" GROUP BY {group_by}"
    
    result = {}
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, tuple(params)) as cur:
            rows = await cur.fetchall()
            for r in rows:
                result[r[group_by]] = r['total']
    return result

async def get_tax_payments_history(
    company_id: str,
    jurisdiction: str = None,
    year: int = None
) -> list[dict]:
    """Get history of tax payments made."""
    query = "SELECT * FROM transactions WHERE company_id = ? AND transaction_type = 'tax_payment'"
    params = [company_id]
    
    if jurisdiction:
        query += " AND jurisdiction = ?"
        params.append(jurisdiction)
    if year:
        query += " AND transaction_date LIKE ?"
        params.append(f"{year}-%")
        
    query += " ORDER BY transaction_date DESC"
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, tuple(params)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

async def get_document_financial_data(
    company_id: str,
    jurisdiction: str,
    obligation_id: str,
    period: str
) -> dict:
    """Assemble the complete financial data package needed to generate
    a specific compliance document.
    """
    summary = await get_financial_summary(company_id, jurisdiction, period)
    
    # We load the data from KB and cross reference
    kb = load_knowledge_base()
    jur_data = kb.get("jurisdictions", {}).get(jurisdiction, {})
    obs = jur_data.get("obligations", [])
    
    doc_type = "unknown"
    tax_rate = 0.0
    for ob in obs:
        if ob["id"] == obligation_id:
            doc_type = ob.get("output_type")
            tax_rate = ob.get("tax_rate", 0.0)
            break
            
    # Depending on doc_type, repackage the summary logically
    # Essentially this maps to the format our old doc generator expected but using REAL DB numbers
    # To interop cleanly with `generate_document` function we defined earlier:
    
    # generate_document() expects financial_data dict with annual_revenue if using mock approach
    # Since we are modifying to use real data, we package it neatly here
    return {
        "period": period,
        "doc_type": doc_type,
        "tax_rate": tax_rate,
        **summary
    }
