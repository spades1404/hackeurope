"""Invoice Reconciliation Agent — LangGraph workflow with Langfuse tracing.

Per-transaction flow:
1. LLM generates Gmail search query from transaction data
2. Gmail API searches for matching email, downloads top PDF
3. Vision model extracts structured invoice data from PDF
4. Deterministic matching engine scores transaction ↔ invoice
5. Returns match proposal with confidence and reasoning

All steps traced in Langfuse.
"""

import logging
import time
from typing import TypedDict

from langgraph.graph import END, StateGraph

import config
from models.schemas import (
    EmailInvoice,
    MatchProposal,
    MatchStatus,
    ReconciliationResult,
    Transaction,
)
from services.gmail_service import GmailService
from services.invoice_extractor import extract_invoice_data
from services.matching_engine import score_match
from services.search_query_builder import build_search_query

logger = logging.getLogger(__name__)

# --- Langfuse setup ---

_langfuse = None


def _get_langfuse():
    global _langfuse
    if _langfuse is None and config.LANGFUSE_ENABLED:
        from langfuse import Langfuse

        _langfuse = Langfuse(
            public_key=config.LANGFUSE_PUBLIC_KEY,
            secret_key=config.LANGFUSE_SECRET_KEY,
            host=config.LANGFUSE_HOST,
        )
    return _langfuse


# --- LangGraph State ---

class AgentState(TypedDict):
    transaction: Transaction
    gmail_query: str | None
    gmail_query_reasoning: str | None
    email_invoice: EmailInvoice | None
    match_proposal: MatchProposal | None
    emails_found: int
    error: str | None
    trace_id: str | None


# --- Node functions ---

def generate_search_query(state: AgentState) -> dict:
    """Node 1: Generate Gmail search query from transaction data."""
    txn = state["transaction"]
    trace_id = state.get("trace_id")

    langfuse = _get_langfuse()
    span = None
    if langfuse and trace_id:
        span = langfuse.span(
            trace_id=trace_id,
            name="generate_search_query",
            input={"transaction_id": txn.id, "counterparty": txn.counterparty_name},
        )

    try:
        start = time.time()
        result = build_search_query(
            transaction_date=txn.date.isoformat(),
            amount=txn.amount,
            currency=txn.currency,
            counterparty_name=txn.counterparty_name,
            iban=txn.counterparty_iban,
            reference=txn.reference,
        )
        duration = time.time() - start

        if span:
            span.end(
                output=result,
                metadata={"duration_s": round(duration, 2), "model": config.SEARCH_QUERY_MODEL},
            )

        return {
            "gmail_query": result["query"],
            "gmail_query_reasoning": result.get("reasoning", ""),
        }

    except Exception as e:
        logger.error(f"Search query generation failed for txn {txn.id}: {e}")
        if span:
            span.end(output={"error": str(e)}, level="ERROR")
        return {"error": f"Search query generation failed: {e}"}


def search_gmail(state: AgentState) -> dict:
    """Node 2: Search Gmail and download the top matching PDF."""
    query = state.get("gmail_query")
    if not query:
        return {"error": "No Gmail query available"}

    txn = state["transaction"]
    trace_id = state.get("trace_id")

    langfuse = _get_langfuse()
    span = None
    if langfuse and trace_id:
        span = langfuse.span(
            trace_id=trace_id,
            name="search_gmail",
            input={"query": query, "transaction_id": txn.id},
        )

    try:
        start = time.time()
        gmail = GmailService()
        email_invoice = gmail.find_invoice_email(query)
        duration = time.time() - start

        if email_invoice:
            if span:
                span.end(
                    output={
                        "found": True,
                        "email_id": email_invoice.email_id,
                        "from": email_invoice.email_from,
                        "subject": email_invoice.email_subject,
                        "filename": email_invoice.filename,
                    },
                    metadata={"duration_s": round(duration, 2)},
                )
            return {"email_invoice": email_invoice, "emails_found": 1}
        else:
            if span:
                span.end(output={"found": False}, metadata={"duration_s": round(duration, 2)})
            return {"emails_found": 0, "error": "No matching email with PDF found"}

    except Exception as e:
        logger.error(f"Gmail search failed for txn {txn.id}: {e}")
        if span:
            span.end(output={"error": str(e)}, level="ERROR")
        return {"error": f"Gmail search failed: {e}"}


def extract_invoice(state: AgentState) -> dict:
    """Node 3: Extract structured data from the invoice PDF."""
    email_inv = state.get("email_invoice")
    if not email_inv:
        return {"error": "No email invoice to extract"}

    txn = state["transaction"]
    trace_id = state.get("trace_id")

    langfuse = _get_langfuse()
    span = None
    if langfuse and trace_id:
        span = langfuse.span(
            trace_id=trace_id,
            name="extract_invoice",
            input={
                "transaction_id": txn.id,
                "filename": email_inv.filename,
                "email_from": email_inv.email_from,
            },
        )

    try:
        start = time.time()
        extracted = extract_invoice_data(email_inv.pdf_base64)
        duration = time.time() - start

        email_inv.extracted_data = extracted

        if span:
            span.end(
                output={
                    "vendor": extracted.vendor_name,
                    "amount": extracted.gross_amount,
                    "invoice_number": extracted.invoice_number,
                },
                metadata={"duration_s": round(duration, 2), "model": config.EXTRACTION_MODEL},
            )

        return {"email_invoice": email_inv}

    except Exception as e:
        logger.error(f"Invoice extraction failed for txn {txn.id}: {e}")
        if span:
            span.end(output={"error": str(e)}, level="ERROR")
        return {"error": f"Invoice extraction failed: {e}"}


def match_transaction(state: AgentState) -> dict:
    """Node 4: Score the match between transaction and extracted invoice."""
    email_inv = state.get("email_invoice")
    if not email_inv or not email_inv.extracted_data:
        return {"error": "No extracted invoice data to match"}

    txn = state["transaction"]
    trace_id = state.get("trace_id")

    langfuse = _get_langfuse()
    span = None
    if langfuse and trace_id:
        span = langfuse.span(
            trace_id=trace_id,
            name="match_transaction",
            input={"transaction_id": txn.id},
        )

    try:
        start = time.time()
        proposal = score_match(txn, email_inv.extracted_data)
        proposal.email_id = email_inv.email_id
        duration = time.time() - start

        if span:
            span.end(
                output={
                    "confidence": proposal.confidence_score,
                    "status": proposal.status.value,
                    "reasons": proposal.match_reasons,
                },
                metadata={"duration_s": round(duration, 2)},
            )

        return {"match_proposal": proposal}

    except Exception as e:
        logger.error(f"Matching failed for txn {txn.id}: {e}")
        if span:
            span.end(output={"error": str(e)}, level="ERROR")
        return {"error": f"Matching failed: {e}"}


def should_continue_after_search(state: AgentState) -> str:
    """Route after Gmail search: continue if email found, else end."""
    if state.get("error") or not state.get("email_invoice"):
        return "no_match"
    return "continue"


# --- Graph ---

def build_graph() -> StateGraph:
    """Build the per-transaction reconciliation LangGraph."""
    workflow = StateGraph(AgentState)

    workflow.add_node("generate_query", generate_search_query)
    workflow.add_node("search_gmail", search_gmail)
    workflow.add_node("extract_invoice", extract_invoice)
    workflow.add_node("match", match_transaction)

    workflow.set_entry_point("generate_query")
    workflow.add_edge("generate_query", "search_gmail")
    workflow.add_conditional_edges(
        "search_gmail",
        should_continue_after_search,
        {"continue": "extract_invoice", "no_match": END},
    )
    workflow.add_edge("extract_invoice", "match")
    workflow.add_edge("match", END)

    return workflow.compile()


# --- Public API ---

_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def reconcile_transaction(transaction: Transaction) -> ReconciliationResult:
    """Reconcile a single transaction: find matching invoice in Gmail.

    This is the main entry point. Creates a Langfuse trace for the full run.
    """
    langfuse = _get_langfuse()
    trace = None
    trace_id = None

    if langfuse:
        trace = langfuse.trace(
            name="reconcile_transaction",
            input={
                "transaction_id": transaction.id,
                "counterparty": transaction.counterparty_name,
                "amount": transaction.amount,
                "date": transaction.date.isoformat(),
            },
            metadata={"currency": transaction.currency},
        )
        trace_id = trace.id

    initial_state: AgentState = {
        "transaction": transaction,
        "gmail_query": None,
        "gmail_query_reasoning": None,
        "email_invoice": None,
        "match_proposal": None,
        "emails_found": 0,
        "error": None,
        "trace_id": trace_id,
    }

    graph = get_graph()
    final_state = graph.invoke(initial_state)

    # Build result
    proposal = final_state.get("match_proposal")
    error = final_state.get("error")

    if proposal:
        status = proposal.status.value
    elif error:
        status = "error"
    else:
        status = "no_match"

    result = ReconciliationResult(
        transaction_id=transaction.id,
        status=status,
        match_proposal=proposal,
        gmail_query_used=final_state.get("gmail_query"),
        emails_found=final_state.get("emails_found", 0),
        error=error,
    )

    if trace:
        trace.update(
            output={
                "status": result.status,
                "confidence": proposal.confidence_score if proposal else None,
                "emails_found": result.emails_found,
            },
        )

    logger.info(
        f"Transaction {transaction.id} ({transaction.counterparty_name}): "
        f"status={result.status}, "
        f"confidence={proposal.confidence_score if proposal else 'N/A'}"
    )

    return result


def reconcile_batch(transactions: list[Transaction]) -> list[ReconciliationResult]:
    """Reconcile a batch of transactions sequentially.

    For production, consider using async/parallel execution.
    """
    results = []
    for i, txn in enumerate(transactions):
        logger.info(f"--- Reconciling {i+1}/{len(transactions)}: {txn.counterparty_name} ---")
        result = reconcile_transaction(txn)
        results.append(result)

    # Summary
    matched = sum(1 for r in results if r.status == "matched")
    review = sum(1 for r in results if r.status == "needs_review")
    no_match = sum(1 for r in results if r.status == "no_match")
    errors = sum(1 for r in results if r.status == "error")

    logger.info(
        f"\n=== Batch complete: {len(results)} transactions ===\n"
        f"  Matched:      {matched}\n"
        f"  Needs review:  {review}\n"
        f"  No match:      {no_match}\n"
        f"  Errors:        {errors}"
    )

    # Flush Langfuse
    langfuse = _get_langfuse()
    if langfuse:
        langfuse.flush()

    return results
