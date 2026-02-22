"""FastAPI server for the Invoice Reconciliation Agent.

Endpoints:
- POST /reconcile           — Reconcile a batch of transactions
- GET  /reconcile/{txn_id}  — Get result for a specific transaction
- POST /reconcile/feedback  — Accept/reject a match proposal (for Iteration 2 UI)
- GET  /health              — Health check
"""

import logging
import uuid
from datetime import date

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.reconciliation_agent import reconcile_batch
from models.schemas import MatchProposal, MatchStatus, ReconciliationResult, Transaction

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="Invoice Reconciliation Agent",
    description="AI-powered invoice matching: Gmail → OCR → transaction reconciliation",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory results store (swap for DB in production)
_results_store: dict[str, ReconciliationResult] = {}


# --- Request / Response models ---

class TransactionInput(BaseModel):
    id: str | None = None
    date: date
    amount: float
    currency: str = "EUR"
    counterparty_name: str
    counterparty_iban: str | None = None
    reference: str | None = None
    customer_id: str = "unknown"  # PAID billing customer identifier


class ReconcileRequest(BaseModel):
    transactions: list[TransactionInput]


class ReconcileSummary(BaseModel):
    total: int
    matched: int
    needs_review: int
    no_match: int
    errors: int
    results: list[ReconciliationResult]


class FeedbackInput(BaseModel):
    transaction_id: str
    decision: str  # "accept" | "reject"


# --- Endpoints ---

@app.get("/health")
def health():
    return {"status": "ok", "service": "invoice-reconciliation-agent"}


@app.post("/reconcile", response_model=ReconcileSummary)
def reconcile(request: ReconcileRequest):
    """Run reconciliation on a batch of transactions."""
    transactions = []
    for t in request.transactions:
        transactions.append(
            Transaction(
                id=t.id or str(uuid.uuid4()),
                date=t.date,
                amount=t.amount,
                currency=t.currency,
                counterparty_name=t.counterparty_name,
                counterparty_iban=t.counterparty_iban,
                reference=t.reference,
                customer_id=t.customer_id,
            )
        )

    results = reconcile_batch(transactions)

    # Store results
    for r in results:
        _results_store[r.transaction_id] = r

    return ReconcileSummary(
        total=len(results),
        matched=sum(1 for r in results if r.status == "matched"),
        needs_review=sum(1 for r in results if r.status == "needs_review"),
        no_match=sum(1 for r in results if r.status == "no_match"),
        errors=sum(1 for r in results if r.status == "error"),
        results=results,
    )


@app.get("/reconcile/{transaction_id}", response_model=ReconciliationResult)
def get_result(transaction_id: str):
    """Get reconciliation result for a specific transaction."""
    if transaction_id not in _results_store:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return _results_store[transaction_id]


@app.post("/reconcile/feedback")
def submit_feedback(feedback: FeedbackInput):
    """Accept or reject a match proposal. Used by the Iteration 2 UI."""
    if feedback.transaction_id not in _results_store:
        raise HTTPException(status_code=404, detail="Transaction not found")

    result = _results_store[feedback.transaction_id]
    if not result.match_proposal:
        raise HTTPException(status_code=400, detail="No match proposal to review")

    if feedback.decision == "accept":
        result.match_proposal.status = MatchStatus.MATCHED
        result.status = "matched"
    elif feedback.decision == "reject":
        result.match_proposal.status = MatchStatus.REJECTED
        result.status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="Decision must be 'accept' or 'reject'")

    return {"transaction_id": feedback.transaction_id, "new_status": result.status}


if __name__ == "__main__":
    import uvicorn
    import config

    uvicorn.run(app, host=config.HOST, port=config.PORT)
