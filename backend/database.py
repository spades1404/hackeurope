import aiosqlite
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "tunatax.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL, -- 'worker' or 'business'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        await db.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            name TEXT NOT NULL,
            profile JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        ''')
        
        await db.execute('''
        CREATE TABLE IF NOT EXISTS actions (
            id TEXT PRIMARY KEY,
            company_id TEXT,
            obligation_id TEXT,
            obligation_name TEXT,
            jurisdiction TEXT,
            deadline DATE,
            prep_start_date DATE,
            status TEXT,
            priority TEXT,
            document_id TEXT,
            action_data JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )
        ''')

        await db.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            action_id TEXT,
            company_id TEXT,
            document_type TEXT,
            content JSON,
            status TEXT,
            version INT,
            approved_at TIMESTAMP,
            submitted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(action_id) REFERENCES actions(id),
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )
        ''')

        await db.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT,
            role TEXT,
            content TEXT,
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )
        ''')

        await db.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            company_id TEXT,
            jurisdiction TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            category TEXT,
            description TEXT,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            transaction_date DATE NOT NULL,
            quarter TEXT,
            tax_relevant BOOLEAN DEFAULT TRUE,
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )
        ''')

        await db.execute('''
        CREATE TABLE IF NOT EXISTS financial_summaries (
            id TEXT PRIMARY KEY,
            company_id TEXT,
            jurisdiction TEXT NOT NULL,
            period TEXT NOT NULL,
            period_type TEXT NOT NULL,
            summary JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(company_id) REFERENCES companies(id),
            UNIQUE(company_id, jurisdiction, period)
        )
        ''')

        await db.execute('''
        CREATE TABLE IF NOT EXISTS agent_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT,
            action_type TEXT NOT NULL,
            input_summary TEXT,
            output_summary TEXT,
            code_executed TEXT,
            execution_result TEXT,
            duration_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        await db.execute('''
        CREATE TABLE IF NOT EXISTS scheduler_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            actions_checked INTEGER,
            documents_generated INTEGER,
            overdue_marked INTEGER,
            escalated INTEGER,
            errors TEXT
        )
        ''')
        await db.commit()

async def create_user(user_id: str, email: str, name: str, role: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (id, email, name, role) VALUES (?, ?, ?, ?)",
            (user_id, email, name, role)
        )
        await db.commit()

async def get_user(user_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

async def create_company(company_id: str, user_id: str, name: str, profile: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO companies (id, user_id, name, profile) VALUES (?, ?, ?, ?)",
            (company_id, user_id, name, json.dumps(profile))
        )
        await db.commit()

async def seed_demo_transactions(company_id: str, profile: dict):
    """Seed the database with ~50 realistic transactions for a demo company."""
    import uuid
    import random
    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta

    jurisdictions = profile.get("jurisdictions", ["US"])
    revenue_base = profile.get("annual_revenue", 1000000)
    monthly_rev_avg = revenue_base / 12

    transactions = []
    end_date = datetime.now().date()
    start_date = end_date - relativedelta(months=5)

    curr_date = start_date
    while curr_date <= end_date:
        quarter_str = f"{curr_date.year}-Q{(curr_date.month-1)//3 + 1}"
        for jur in jurisdictions:
            # Country params
            currency = "USD"
            if jur == "UK": currency = "GBP"
            elif jur == "DE": currency = "EUR"
            elif jur == "AU": currency = "AUD"
            
            # 1-3 Revenue entries
            for i in range(random.randint(1, 3)):
                amount = monthly_rev_avg * random.uniform(0.2, 0.5)
                transactions.append((
                    str(uuid.uuid4()), company_id, jur, "revenue", "sales", 
                    f"Product Sales {jur} #{random.randint(1000, 9999)}", amount, 
                    currency, curr_date.isoformat(), quarter_str, True, "{}"
                ))
            
            # VAT/GST Collection
            if jur in ["UK", "DE", "AU"]:
                rate = 0.20 if jur == "UK" else 0.19 if jur == "DE" else 0.10
                vat_amount = monthly_rev_avg * rate * random.uniform(0.8, 1.0)
                transactions.append((
                    str(uuid.uuid4()), company_id, jur, "vat_collected", "sales_tax", 
                    f"VAT/GST Collected {jur}", vat_amount, 
                    currency, curr_date.isoformat(), quarter_str, True, "{}"
                ))

            # Expenses (COGS & OpEx)
            for cat in ["cost_of_goods_sold", "operating_expense", "admin", "software"]:
                amount = monthly_rev_avg * random.uniform(0.05, 0.2)
                transactions.append((
                    str(uuid.uuid4()), company_id, jur, "expense", cat, 
                    f"{cat.replace('_', ' ').title()} - {jur}", amount, 
                    currency, curr_date.isoformat(), quarter_str, True, "{}"
                ))

            # Payroll & Withholding
            payroll_amount = monthly_rev_avg * 0.15
            transactions.append((
                str(uuid.uuid4()), company_id, jur, "payroll", "salary", 
                f"Monthly Payroll {jur}", payroll_amount, 
                currency, curr_date.isoformat(), quarter_str, True, "{}"
            ))
            
            # Random tax payments occasionally
            if curr_date.month in [4, 7, 10, 1]:
                tax_amount = monthly_rev_avg * 0.1 * random.uniform(0.9, 1.1)
                transactions.append((
                    str(uuid.uuid4()), company_id, jur, "tax_payment", "estimated_tax", 
                    f"Quarterly Estimated Tax {jur}", tax_amount, 
                    currency, curr_date.isoformat(), quarter_str, True, "{}"
                ))

        # Advance one month
        curr_date += relativedelta(months=1)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(
            """INSERT INTO transactions 
            (id, company_id, jurisdiction, transaction_type, category, description, amount, currency, transaction_date, quarter, tax_relevant, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            transactions
        )
        await db.commit()

async def get_company(company_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM companies WHERE id = ?", (company_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

async def list_companies() -> list[dict]:
    """Return all companies."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM companies") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def create_actions_batch(actions: list):
    async with aiosqlite.connect(DB_PATH) as db:
        for action in actions:
            await db.execute(
                """INSERT INTO actions (id, company_id, obligation_id, obligation_name, jurisdiction, deadline, prep_start_date, status, priority, action_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (action['id'], action['company_id'], action['obligation_id'], action['obligation_name'], action['jurisdiction'], action['deadline'], action['prep_start_date'], action['status'], action['priority'], json.dumps(action.get('action_data', {})))
            )
        await db.commit()

async def get_actions(company_id: str, status: str = None, priority: str = None, jurisdiction: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM actions WHERE company_id = ?"
        params = [company_id]
        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        if jurisdiction:
            query += " AND jurisdiction = ?"
            params.append(jurisdiction)
            
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def list_actions(company_id: str) -> list[dict]:
    return await get_actions(company_id=company_id)

async def get_action(action_id: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM actions WHERE id = ?", (action_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

async def update_action_status(action_id: str, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE actions SET status = ? WHERE id = ?", (status, action_id))
        await db.commit()

async def update_action_document_id(action_id: str, document_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE actions SET document_id = ? WHERE id = ?", (document_id, action_id))
        await db.commit()

async def update_action_document(action_id: str, document_id: str):
    return await update_action_document_id(action_id, document_id)

async def update_action_priority(action_id: str, priority: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE actions SET priority = ? WHERE id = ?", (priority, action_id))
        await db.commit()

async def create_document(doc_id: str, action_id: str, company_id: str, document_type: str, content: dict, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO documents (id, action_id, company_id, document_type, content, status, version) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (doc_id, action_id, company_id, document_type, json.dumps(content), status, 1)
        )
        await db.commit()

async def get_document(doc_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

async def update_document_status(doc_id: str, status: str, timestamp_field: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        if timestamp_field:
            query = f"UPDATE documents SET status = ?, {timestamp_field} = CURRENT_TIMESTAMP WHERE id = ?"
        else:
            query = "UPDATE documents SET status = ? WHERE id = ?"
            
        await db.execute(query, (status, doc_id))
        await db.commit()

async def add_chat_message(company_id: str, role: str, content: str, metadata: dict = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO chat_messages (company_id, role, content, metadata) VALUES (?, ?, ?, ?)",
            (company_id, role, content, json.dumps(metadata or {}))
        )
        await db.commit()

async def get_chat_history(company_id: str, limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM chat_messages WHERE company_id = ? ORDER BY created_at ASC LIMIT ?", (company_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
