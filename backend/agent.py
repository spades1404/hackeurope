import os
import json
import asyncio
from datetime import datetime, timedelta

from backend.database import get_company, get_actions, create_document, get_document, add_chat_message, update_action_document_id
from backend.compliance_engine import load_knowledge_base, load_obligation
from backend.data_access import (
    get_financial_summary,
    get_transactions,
    get_transaction_aggregates,
    get_tax_payments_history,
    get_document_financial_data,
)
from backend.sandbox_executor import execute_analysis
from backend.doc_sandbox import generate_document_via_ai
from backend.llm_provider import chat_with_tools, chat
from typing import Optional
import uuid

# --- Existing compliance tools ---
def get_compliance_plan(company_id: str) -> dict:
    """Gets the overview of the compliance plan and action items for the given company."""
    pass

def get_upcoming_deadlines(company_id: str, days_ahead: int) -> list:
    """Gets a filtered list of upcoming deadlines for the company."""
    pass

def lookup_tax_info(jurisdiction: str, topic: str) -> str:
    """Looks up specific tax information from the internal knowledge base."""
    pass

# --- New data tools ---
def query_transactions(
    company_id: str,
    jurisdiction: Optional[str] = None,
    transaction_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_amount: Optional[float] = None,
    category: Optional[str] = None
) -> list:
    """Search and filter company transactions from the database."""
    pass

def get_period_financials(
    company_id: str,
    jurisdiction: str,
    period: str
) -> dict:
    """Get aggregated financial data for a jurisdiction and period."""
    pass

def generate_compliance_document(
    company_id: str,
    action_id: str
) -> dict:
    """Generate a tax filing document using AI. The AI writes a computation script, executes it against real financial data, and produces a draft document for review."""
    pass

def run_analysis(
    company_id: str,
    code: str,
    data_scope: str = "summary"
) -> dict:
    """Run a custom Python analysis on company financial data."""
    pass

# --- Tool implementations ---
async def execute_get_compliance_plan(company_id: str) -> dict:
    actions = await get_actions(company_id=company_id)
    if not actions:
        return {"error": "No actions found for company."}
    return {
        "total_actions": len(actions),
        "actions": [
            {
                "id": a['id'], "obligation_name": a['obligation_name'],
                "jurisdiction": a['jurisdiction'], "deadline": a['deadline'], "status": a['status']
            } for a in actions[:10]
        ]
    }

async def execute_get_upcoming_deadlines(company_id: str, days_ahead: int = 90) -> list:
    actions = await get_actions(company_id=company_id)
    target_date = datetime.now() + timedelta(days=days_ahead)
    
    upcoming = []
    for a in actions:
        try:
            d = datetime.fromisoformat(a['deadline'])
            if datetime.now() <= d <= target_date:
                upcoming.append({
                    "id": a['id'],
                    "name": a['obligation_name'],
                    "jurisdiction": a['jurisdiction'],
                    "deadline": a['deadline']
                })
        except:
            pass
    return upcoming

async def execute_lookup_tax_info(jurisdiction: str, topic: str) -> str:
    kb = load_knowledge_base()
    jur_data = kb.get('jurisdictions', {}).get(jurisdiction)
    if not jur_data:
        return f"Jurisdiction {jurisdiction} not found."
    return json.dumps(jur_data.get('obligations', []))

async def execute_query_transactions(**kwargs) -> list:
    return await get_transactions(**kwargs)

async def execute_get_period_financials(company_id: str, jurisdiction: str, period: str) -> dict:
    return await get_financial_summary(company_id, jurisdiction, period)

async def execute_generate_compliance_document(company_id: str, action_id: str) -> dict:
    import aiosqlite
    from backend.database import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM actions WHERE id = ?", (action_id,)) as cur:
            action_row = await cur.fetchone()
            if not action_row:
                return {"error": "Action not found."}
            action = dict(action_row)
            action['action_data'] = json.loads(action['action_data'])
    
    company = await get_company(action['company_id'])
    profile = json.loads(company['profile'])
    
    obligation = load_obligation(action["obligation_id"])
    
    # NEW: Fetch real data for this jurisdiction and the action's quarter
    curr_date = datetime.now() # for demo, assume quarter based on today
    quarter_str = f"{curr_date.year}-Q{(curr_date.month-1)//3 + 1}"
    
    real_fin_data = await get_document_financial_data(
        company_id, action['jurisdiction'], action['obligation_id'], quarter_str
    )
    
    transactions = await get_transactions(
        company_id, jurisdiction=action['jurisdiction'], limit=500
    )
    
    # Ask sandbox to generate via LLM
    doc = await generate_document_via_ai(
        obligation=obligation,
        company_profile=profile,
        financial_data=real_fin_data,
        transactions=transactions,
        llm_chat_fn=chat,
    )
    
    if "error" in doc:
        return {"error": doc["error"]}
    
    # Attach data sources meta for frontend
    if "metadata" not in doc:
        doc["metadata"] = {}
    doc["metadata"]["data_sources"] = f"Real DB Data - {quarter_str} - {action['jurisdiction']}"
    
    doc_id = str(uuid.uuid4())
    await create_document(doc_id, action_id, action['company_id'], doc.get('document_type', 'tax_return'), doc, 'draft')
    await update_action_document_id(action_id, doc_id)
    
    # Update action status
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE actions SET status = 'pending_review' WHERE id = ?", (action_id,))
        await db.commit()
    
    return {"success": True, "document_id": doc_id, "message": f"Generated {doc.get('title', 'Document')} via AI sandbox."}

async def execute_run_analysis(company_id: str, code: str, data_scope: str = "summary") -> dict:
    company = await get_company(company_id)
    profile = json.loads(company['profile']) if company else {}
    
    data_context = {"company": profile}
    
    if data_scope == "full":
        data_context["transactions"] = await get_transactions(company_id, limit=5000)
    else:
        # Load summaries across all jurisdictions for the current year
        curr_year = str(datetime.now().year)
        summary = {}
        for jur in profile.get('jurisdictions', []):
            summary[jur] = await get_financial_summary(company_id, jur, f"{curr_year}-annual")
        data_context["summary"] = summary
        
    return await execute_analysis(code, data_context, company_id)

TOOL_FUNCTIONS = {
    "get_compliance_plan": execute_get_compliance_plan,
    "get_upcoming_deadlines": execute_get_upcoming_deadlines,
    "lookup_tax_info": execute_lookup_tax_info,
    "query_transactions": execute_query_transactions,
    "get_period_financials": execute_get_period_financials,
    "generate_compliance_document": execute_generate_compliance_document,
    "run_analysis": execute_run_analysis
}

async def execute_tool(name: str, args: dict):
    if name in TOOL_FUNCTIONS:
        return await TOOL_FUNCTIONS[name](**args)
    return {"error": f"Tool {name} not found"}

# --- OpenAI Format Tools definition ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_compliance_plan",
            "description": "Gets the overview of the compliance plan and action items for the given company.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_id": {"type": "string"}
                },
                "required": ["company_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_deadlines",
            "description": "Gets a filtered list of upcoming deadlines for the company.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_id": {"type": "string"},
                    "days_ahead": {"type": "integer"}
                },
                "required": ["company_id", "days_ahead"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_tax_info",
            "description": "Looks up specific tax information from the internal knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jurisdiction": {"type": "string"},
                    "topic": {"type": "string"}
                },
                "required": ["jurisdiction", "topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_transactions",
            "description": "Search and filter company transactions from the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_id": {"type": "string"},
                    "jurisdiction": {"type": "string"},
                    "transaction_type": {"type": "string"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "min_amount": {"type": "number"},
                    "category": {"type": "string"}
                },
                "required": ["company_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_period_financials",
            "description": "Get aggregated financial data for a jurisdiction and period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_id": {"type": "string"},
                    "jurisdiction": {"type": "string"},
                    "period": {"type": "string"}
                },
                "required": ["company_id", "jurisdiction", "period"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_compliance_document",
            "description": "Generate a tax filing document using AI. The AI writes a computation script, executes it against real financial data, and produces a draft document for review.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_id": {"type": "string", "description": "Company identifier"},
                    "action_id": {"type": "string", "description": "The compliance action/obligation ID"}
                },
                "required": ["company_id", "action_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_analysis",
            "description": "Run a custom Python analysis on company financial data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_id": {"type": "string"},
                    "code": {"type": "string"},
                    "data_scope": {"type": "string", "enum": ["summary", "full"]}
                },
                "required": ["company_id", "code"]
            }
        }
    }
]

async def chat_with_agent(company_id: str, message: str, chat_history: list = None) -> str:
    system_instruction = (
        "You are an AI tax compliance assistant for multinational businesses. "
        "Be helpful, proactive, and precise. Always reference specific jurisdictions, form numbers, and deadlines. "
        "Suggest tools like generating documents when appropriate. "
        "If you are unsure, flag that professional advice is needed.\n\n"
        "## Data Access\n"
        "You have access to the company's financial transaction database. Use these tools:\n"
        "- `query_transactions`: Search/filter individual transactions.\n"
        "- `get_period_financials`: Get pre-aggregated totals for a jurisdiction + period.\n"
        "- `generate_compliance_document`: Generate a compliance document using REAL financial data from the database. Always use this explicitly if asked to generate a document.\n"
        "- `run_analysis`: For complex ad-hoc analysis that doesn't fit the other tools. You write Python code that runs against pre-loaded data. Available variables: `transactions` (list of dicts), `summary` (aggregated dict), `company` (profile dict). Use print() to output.\n\n"
        "**Rules:**\n"
        "- Prefer `get_period_financials` over `query_transactions` when you just need totals\n"
        "- Only use `run_analysis` when the other tools can't answer the question\n"
        "- When using `run_analysis`, keep code simple and always print() results\n"
        "- Never hardcode financial numbers — always pull from the database"
    )
    
    messages = chat_history or []
    messages.append({"role": "user", "content": message})
    
    result = await chat_with_tools(
        messages=messages,
        system=system_instruction,
        tools=TOOLS,
        tool_executor=execute_tool,
    )
    
    if result.get("error"):
        return result.get("content", "Error communicating with LLM.")
        
    return result["content"]
