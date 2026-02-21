from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager
from typing import List, Optional
from pydantic import BaseModel
import uuid
import json

from backend.models import UserModel, CompanyProfile, ActionModel, DocumentPayload, ChatMessage
from backend import database
from backend.compliance_engine import generate_compliance_plan
from backend.document_generator import generate_document
from backend.agent import chat_with_agent
from backend.pdf_export import render_document_to_pdf
import asyncio
from fastapi.staticfiles import StaticFiles
from backend.scheduler import scheduler_loop, run_check_cycle
from backend.doc_sandbox import generate_document_via_ai
from backend import llm_provider
from backend.data_access import get_transactions, get_document_financial_data
from backend.compliance_engine import load_obligation
from datetime import datetime
import os

async def shared_agent_generate(company_id, action_id):
    action = await database.get_action(action_id)
    company = await database.get_company(company_id)
    obligation = load_obligation(action["obligation_id"])
    
    curr_date = datetime.now()
    quarter_str = f"{curr_date.year}-Q{(curr_date.month-1)//3 + 1}"
    
    financials = await get_document_financial_data(
        company_id, action["jurisdiction"], action["obligation_id"], action.get("period", quarter_str)
    )
    transactions = await get_transactions(
        company_id, jurisdiction=action["jurisdiction"], limit=500
    )
    return await generate_document_via_ai(
        obligation=obligation,
        company_profile=json.loads(company["profile"]),
        financial_data=financials,
        transactions=transactions,
        llm_chat_fn=llm_provider.chat,
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB on startup
    await database.init_db()
    
    scheduler_task = asyncio.create_task(
        scheduler_loop(database, shared_agent_generate)
    )
    
    yield
    
    scheduler_task.cancel()

app = FastAPI(title="Tax API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/users", response_model=UserModel)
async def create_user_endpoint(user: UserModel):
    if not user.id:
        user.id = str(uuid.uuid4())
    
    await database.create_user(user.id, user.email, user.name, user.role)
    return user

@app.get("/api/users/{user_id}", response_model=UserModel)
async def get_user_endpoint(user_id: str):
    user = await database.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserModel(**user)

@app.post("/api/companies", response_model=CompanyProfile)
async def create_company_endpoint(profile: CompanyProfile):
    if not profile.id:
        profile.id = str(uuid.uuid4())
    
    await database.create_company(profile.id, profile.user_id, profile.name, profile.model_dump(exclude={"user_id"}))
    
    # Auto-generate plan
    plan = generate_compliance_plan(profile.model_dump())
    actions = plan.get("actions", [])
    if actions:
        for a in actions:
            a["company_id"] = profile.id
        await database.create_actions_batch(actions)

    # Seed demo financials
    await database.seed_demo_transactions(profile.id, profile.model_dump())
        
    return profile

@app.get("/api/companies/{company_id}", response_model=CompanyProfile)
async def get_company_endpoint(company_id: str):
    company = await database.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    profile = json.loads(company['profile'])
    profile['id'] = company['id']
    return CompanyProfile(**profile)

@app.get("/api/companies/{company_id}/plan")
async def get_company_plan_endpoint(company_id: str):
    company = await database.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    profile = json.loads(company['profile'])
    plan = generate_compliance_plan(profile)
    return plan

@app.get("/api/companies/{company_id}/actions")
async def list_actions_endpoint(
    company_id: str,
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    jurisdiction: Optional[str] = Query(None)
):
    actions = await database.get_actions(company_id, status, priority, jurisdiction)
    for a in actions:
        if isinstance(a.get("action_data"), str):
            a["action_data"] = json.loads(a["action_data"])
    return actions

@app.patch("/api/actions/{action_id}/status")
async def update_action_status_endpoint(action_id: str, status: str = Body(..., embed=True)):
    await database.update_action_status(action_id, status)
    return {"message": "Status updated successfully"}

@app.post("/api/actions/{action_id}/generate-document")
async def generate_document_endpoint(action_id: str):
    import aiosqlite
    from backend.database import DB_PATH
    from backend.data_access import get_document_financial_data
    from datetime import datetime
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM actions WHERE id = ?", (action_id,)) as cur:
            row = await cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Action not found")
            action = dict(row)
            action["action_data"] = json.loads(action["action_data"])
            
    company = await database.get_company(action["company_id"])
    profile = json.loads(company['profile'])
    
    # Fetch REAL data
    curr_date = datetime.now()
    quarter_str = f"{curr_date.year}-Q{(curr_date.month-1)//3 + 1}"
    
    real_fin_data = await get_document_financial_data(
        action["company_id"], action['jurisdiction'], action['obligation_id'], quarter_str
    )
    
    doc = generate_document(action, profile, real_fin_data)
    doc["metadata"]["data_sources"] = f"Real DB Data - {quarter_str} - {action['jurisdiction']}"
    
    doc_id = str(uuid.uuid4())
    await database.create_document(doc_id, action_id, action["company_id"], doc["document_type"], doc, "draft")
    await database.update_action_document_id(action_id, doc_id)
    await database.update_action_status(action_id, "pending_review")
    
    return {"document_id": doc_id, "document": doc}

# === Transaction Management (for demo data + future integrations) ===

@app.get("/api/companies/{company_id}/transactions")
async def list_transactions_endpoint(
    company_id: str,
    jurisdiction: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    limit: int = 100
):
    from backend.data_access import get_transactions
    txns = await get_transactions(company_id, jurisdiction, transaction_type, limit=limit)
    return txns

@app.get("/api/companies/{company_id}/financials/{jurisdiction}/{period}")
async def get_financial_summary_endpoint(company_id: str, jurisdiction: str, period: str):
    from backend.data_access import get_financial_summary
    summary = await get_financial_summary(company_id, jurisdiction, period)
    return summary

@app.get("/api/documents/{doc_id}")
async def get_document_endpoint(doc_id: str):
    doc = await database.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc["content"] = json.loads(doc["content"])
    return doc

@app.post("/api/documents/{doc_id}/approve")
async def approve_document_endpoint(doc_id: str):
    await database.update_document_status(doc_id, "approved", "approved_at")
    
    # Cascade to action
    doc = await database.get_document(doc_id)
    if doc:
        await database.update_action_status(doc["action_id"], "approved")
    
    return {"message": "Document approved"}

@app.post("/api/documents/{doc_id}/submit")
async def submit_document_endpoint(doc_id: str):
    await database.update_document_status(doc_id, "submitted", "submitted_at")
    
    # Cascade to action
    doc = await database.get_document(doc_id)
    if doc:
        await database.update_action_status(doc["action_id"], "submitted")
        
    return {"message": "Document submitted"}

@app.get("/api/documents/{doc_id}/pdf")
async def get_document_pdf_endpoint(doc_id: str):
    doc_row = await database.get_document(doc_id)
    if not doc_row:
        raise HTTPException(status_code=404, detail="Document not found")
    
    company_row = await database.get_company(doc_row["company_id"])
    company_name = company_row["name"] if company_row else "Unknown Company"
    
    doc_content = json.loads(doc_row["content"])
    
    pdf_bytes = render_document_to_pdf(doc_content, company_name)
    
    return Response(content=pdf_bytes, media_type="application/pdf")

class ChatRequest(BaseModel):
    message: str

@app.post("/api/companies/{company_id}/chat")
async def chat_endpoint(company_id: str, request: ChatRequest):
    message = request.message
    
    # Save user message
    await database.add_chat_message(company_id, "user", message)
    
    # Get history for context
    history_rows = await database.get_chat_history(company_id, limit=20)
    
    reply = await chat_with_agent(company_id, message, history_rows)
    
    # Save assistant message
    await database.add_chat_message(company_id, "model", reply)
    
    return {"reply": reply}

@app.get("/api/companies/{company_id}/chat/history")
async def get_chat_history_endpoint(company_id: str):
    history_rows = await database.get_chat_history(company_id, limit=50)
    for r in history_rows:
        r["metadata"] = json.loads(r["metadata"])
    return history_rows

@app.post("/api/scheduler/run")
async def run_scheduler_endpoint():
    await run_check_cycle(database, shared_agent_generate)
    return {"message": "Scheduler cycle complete"}

@app.get("/api/scheduler/status")
async def scheduler_status_endpoint():
    return {"status": "running"}

@app.get("/health")
async def health():
    return {"status": "ok", "provider": llm_provider.get_provider(), "model": llm_provider.get_model()}

if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
