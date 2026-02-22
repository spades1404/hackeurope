"""Invoice Reconciliation Agent — LangGraph workflow with Langfuse tracing.

Per-transaction flow:
1. generate_query          — LLM generates a Gmail search query from transaction data
2. search_gmail_metadata   — Gmail API fetches metadata for all matching emails
                             (no PDFs downloaded yet)
                             If 0 results: retries once with a broader fallback query
3. pre_filter_candidates   — scores each candidate by sender domain, subject keywords,
                             and date proximity; sorts descending
4. extract_until_confident — iterates through top-ranked candidates in order:
                               a. download PDF
                               b. OCR via vision LLM
                               c. score match
                             stops when confidence >= OCR_CONFIDENCE_TARGET or
                             MAX_OCR_CANDIDATES exhausted; returns best result found
"""

import logging
import time
from typing import TypedDict

from langgraph.graph import END, StateGraph

import config
from schemas import (
    EmailCandidate,
    EmailInvoice,
    MatchProposal,
    MatchStatus,
    ReconciliationResult,
    Transaction,
)
from gmail_service import GmailService
from invoice_extractor import extract_invoice_data
from matching_engine import pre_filter_score, score_match
from search_query_builder import build_broad_fallback_query, build_search_query

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Langfuse setup
# ---------------------------------------------------------------------------

_langfuse = None


def _get_langfuse():
    global _langfuse
    if _langfuse is None and config.LANGFUSE_ENABLED:
        from langfuse import Langfuse
        import litellm

        _langfuse = Langfuse(
            public_key=config.LANGFUSE_PUBLIC_KEY,
            secret_key=config.LANGFUSE_SECRET_KEY,
            host=config.LANGFUSE_HOST,
        )

    return _langfuse


# ---------------------------------------------------------------------------
# PAID setup
# ---------------------------------------------------------------------------

_paid = None


def _get_paid():
    global _paid
    if _paid is None and config.PAID_API_KEY:
        from paid import Paid
        _paid = Paid(token=config.PAID_API_KEY)
    return _paid


# ---------------------------------------------------------------------------
# LangGraph State
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    transaction: Transaction
    gmail_query: str | None
    gmail_query_reasoning: str | None
    # Raw metadata candidates from Gmail search (unsorted, no PDFs)
    email_candidates: list[EmailCandidate]
    # Candidates after pre-filter scoring, sorted descending
    ranked_candidates: list[EmailCandidate]
    # Best email that produced the winning match proposal
    best_email_invoice: EmailInvoice | None
    match_proposal: MatchProposal | None
    emails_found: int
    ocr_candidates_tried: int
    error: str | None


# ---------------------------------------------------------------------------
# Node: generate_query
# ---------------------------------------------------------------------------

def generate_search_query(state: AgentState) -> dict:
    """Node 1: Generate Gmail search query from transaction data."""
    txn = state["transaction"]

    langfuse = _get_langfuse()
    span = None
    if langfuse:
        span = langfuse.start_span(
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
            span.update(
                output=result,
                metadata={"duration_s": round(duration, 2), "model": config.SEARCH_QUERY_MODEL},
            )
            span.end()

        return {
            "gmail_query": result["query"],
            "gmail_query_reasoning": result.get("reasoning", ""),
        }

    except Exception as e:
        logger.error(f"Search query generation failed for txn {txn.id}: {e}")
        if span:
            span.update(output={"error": str(e)})
            span.end()
        return {"error": f"Search query generation failed: {e}"}


# ---------------------------------------------------------------------------
# Node: search_gmail_metadata
# ---------------------------------------------------------------------------

def search_gmail_metadata(state: AgentState) -> dict:
    """Node 2: Search Gmail and fetch metadata for all results — no PDFs downloaded.

    If the primary query returns 0 results, retries once with a broader fallback
    query (no date range, no from: filter).
    """
    query = state.get("gmail_query")
    if not query:
        return {"error": "No Gmail query available", "email_candidates": [], "emails_found": 0}

    txn = state["transaction"]

    langfuse = _get_langfuse()
    span = None
    if langfuse:
        span = langfuse.start_span(
            name="search_gmail_metadata",
            input={"query": query, "transaction_id": txn.id},
        )

    try:
        start = time.time()
        gmail = GmailService()
        candidates = gmail.find_invoice_candidates(query)

        # Retry with a broader query if primary returned nothing
        fallback_used = False
        if not candidates:
            fallback = build_broad_fallback_query(txn.counterparty_name)
            logger.info(
                f"Primary query returned 0 results for txn {txn.id}; "
                f"retrying with broad fallback: {fallback['query']}"
            )
            candidates = gmail.find_invoice_candidates(fallback["query"])
            fallback_used = True

        duration = time.time() - start
        pdf_count = sum(1 for c in candidates if c.has_pdf)

        if span:
            span.update(
                output={
                    "candidates": len(candidates),
                    "with_pdf": pdf_count,
                    "fallback_used": fallback_used,
                },
                metadata={"duration_s": round(duration, 2)},
            )
            span.end()

        return {
            "email_candidates": candidates,
            "emails_found": len(candidates),
        }

    except Exception as e:
        logger.error(f"Gmail metadata search failed for txn {txn.id}: {e}")
        if span:
            span.update(output={"error": str(e)})
            span.end()
        return {
            "error": f"Gmail search failed: {e}",
            "email_candidates": [],
            "emails_found": 0,
        }


# ---------------------------------------------------------------------------
# Node: pre_filter_candidates
# ---------------------------------------------------------------------------

def pre_filter_candidates(state: AgentState) -> dict:
    """Node 3: Score each email candidate by metadata (sender, subject, date).

    Candidates are sorted descending by pre-filter score.  Those below
    PRE_FILTER_MIN_SCORE are kept in the list but will be skipped by the
    OCR loop unless all higher-scored candidates are exhausted.
    """
    candidates: list[EmailCandidate] = state.get("email_candidates", [])
    txn = state["transaction"]

    langfuse = _get_langfuse()
    span = None
    if langfuse:
        span = langfuse.start_span(
            name="pre_filter_candidates",
            input={"transaction_id": txn.id, "candidates": len(candidates)},
        )

    scored = []
    for c in candidates:
        score, reasons = pre_filter_score(txn, c)
        c.pre_filter_score = score
        c.pre_filter_reasons = reasons
        scored.append(c)
        logger.debug(
            f"  [{score:.2f}] {c.email_from!r} | {c.email_subject!r} | "
            f"pdf={c.has_pdf} | inv_date={c.invoice_date_hint}"
        )

    def _date_proximity(c: EmailCandidate) -> float:
        """Days between the invoice date hint (from email body) and the transaction date.

        Falls back to email send date if no hint was extracted.
        Candidates with no date signal at all sort to the end.
        """
        d = c.invoice_date_hint
        if d is None:
            try:
                d = c.email_date.date() if hasattr(c.email_date, "date") else c.email_date
            except Exception:
                return float("inf")
        try:
            return abs((txn.date - d).days)
        except Exception:
            return float("inf")

    # Sort primarily by pre-filter score, then by invoice date proximity to the
    # transaction. Among same-supplier candidates (equal scores), the invoice
    # dated closest to the transaction is tried first through OCR.
    ranked = sorted(scored, key=lambda c: (-c.pre_filter_score, _date_proximity(c)))

    if span:
        top = [
            {"from": c.email_from, "subject": c.email_subject, "score": c.pre_filter_score}
            for c in ranked[:3]
        ]
        span.update(output={"top_candidates": top})
        span.end()

    logger.info(
        f"Pre-filter complete for txn {txn.id}: "
        f"{len(ranked)} candidates, top score={ranked[0].pre_filter_score if ranked else 0:.2f}"
    )
    for i, c in enumerate(ranked[:5]):
        logger.info(
            f"  [{i+1}] score={c.pre_filter_score:.2f} | "
            f"inv_date={c.invoice_date_hint} | {c.email_subject!r}"
        )

    return {"ranked_candidates": ranked}


# ---------------------------------------------------------------------------
# Node: extract_until_confident
# ---------------------------------------------------------------------------

def extract_until_confident(state: AgentState) -> dict:
    """Node 4: Download PDFs and run OCR until confidence target is reached.

    Iterates through ranked_candidates in order.  For each:
      1. Download PDF (deferred until now)
      2. Extract structured data via vision LLM
      3. Score match against transaction

    Stops early when confidence >= OCR_CONFIDENCE_TARGET.
    Returns the best MatchProposal found across all tried candidates.
    """
    ranked: list[EmailCandidate] = state.get("ranked_candidates", [])
    txn = state["transaction"]

    langfuse = _get_langfuse()
    span = None
    if langfuse:
        span = langfuse.start_span(
            name="extract_until_confident",
            input={"transaction_id": txn.id, "candidates_available": len(ranked)},
        )

    gmail = GmailService()
    best_proposal: MatchProposal | None = None
    best_email: EmailInvoice | None = None
    tried = 0

    for candidate in ranked:
        if tried >= config.MAX_OCR_CANDIDATES:
            logger.info(
                f"Reached MAX_OCR_CANDIDATES ({config.MAX_OCR_CANDIDATES}) for txn {txn.id}"
            )
            break

        if candidate.pre_filter_score < config.PRE_FILTER_MIN_SCORE:
            logger.info(
                f"Skipping remaining candidates: pre-filter score "
                f"{candidate.pre_filter_score:.2f} < {config.PRE_FILTER_MIN_SCORE}"
            )
            break

        if not candidate.has_pdf:
            logger.debug(f"Skipping {candidate.email_id}: no PDF")
            continue

        logger.info(
            f"OCR attempt {tried + 1} for txn {txn.id}: "
            f"{candidate.email_from!r} (pre-filter={candidate.pre_filter_score:.2f})"
        )

        # Step a: download PDF
        try:
            email_invoice = gmail.download_pdf_for_candidate(candidate)
        except Exception as e:
            logger.warning(f"PDF download failed for {candidate.email_id}: {e}")
            tried += 1
            continue

        if not email_invoice:
            tried += 1
            continue

        # Step b: extract invoice data via vision LLM
        try:
            extracted = extract_invoice_data(email_invoice.pdf_base64)
        except Exception as e:
            logger.warning(f"OCR extraction failed for {candidate.email_id}: {e}")
            tried += 1
            continue

        email_invoice.extracted_data = extracted

        # Step c: score match
        try:
            proposal = score_match(txn, extracted)
            proposal.email_id = candidate.email_id
        except Exception as e:
            logger.warning(f"Scoring failed for {candidate.email_id}: {e}")
            tried += 1
            continue

        tried += 1

        logger.info(
            f"  → confidence={proposal.confidence_score:.2f} "
            f"status={proposal.status.value} "
            f"(attempt {tried})"
        )

        if best_proposal is None or proposal.confidence_score > best_proposal.confidence_score:
            best_proposal = proposal
            best_email = email_invoice

        if proposal.confidence_score >= config.OCR_CONFIDENCE_TARGET:
            logger.info(
                f"Confidence target {config.OCR_CONFIDENCE_TARGET:.0%} reached after "
                f"{tried} OCR attempt(s) for txn {txn.id}"
            )
            break

    if span:
        span.update(
            output={
                "ocr_attempts": tried,
                "best_confidence": best_proposal.confidence_score if best_proposal else None,
                "status": best_proposal.status.value if best_proposal else "no_match",
            }
        )
        span.end()

    if not best_proposal:
        logger.info(f"No match found after {tried} OCR attempts for txn {txn.id}")

    return {
        "match_proposal": best_proposal,
        "best_email_invoice": best_email,
        "ocr_candidates_tried": tried,
    }


# ---------------------------------------------------------------------------
# Conditional routing
# ---------------------------------------------------------------------------

def should_run_ocr(state: AgentState) -> str:
    """Route after pre-filter: proceed to OCR if any candidates have a PDF,
    otherwise end immediately."""
    if state.get("error"):
        return "no_match"
    ranked: list[EmailCandidate] = state.get("ranked_candidates", [])
    has_viable = any(
        c.has_pdf and c.pre_filter_score >= config.PRE_FILTER_MIN_SCORE
        for c in ranked
    )
    return "continue" if has_viable else "no_match"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Build the per-transaction reconciliation LangGraph."""
    workflow = StateGraph(AgentState)

    workflow.add_node("generate_query", generate_search_query)
    workflow.add_node("search_gmail_metadata", search_gmail_metadata)
    workflow.add_node("pre_filter", pre_filter_candidates)
    workflow.add_node("extract_until_confident", extract_until_confident)

    workflow.set_entry_point("generate_query")
    workflow.add_edge("generate_query", "search_gmail_metadata")
    workflow.add_edge("search_gmail_metadata", "pre_filter")
    workflow.add_conditional_edges(
        "pre_filter",
        should_run_ocr,
        {"continue": "extract_until_confident", "no_match": END},
    )
    workflow.add_edge("extract_until_confident", END)

    return workflow.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def reconcile_transaction(transaction: Transaction) -> ReconciliationResult:
    """Reconcile a single transaction: find matching invoice in Gmail."""
    langfuse = _get_langfuse()

    initial_state: AgentState = {
        "transaction": transaction,
        "gmail_query": None,
        "gmail_query_reasoning": None,
        "email_candidates": [],
        "ranked_candidates": [],
        "best_email_invoice": None,
        "match_proposal": None,
        "emails_found": 0,
        "ocr_candidates_tried": 0,
        "error": None,
    }

    graph = get_graph()

    def _run():
        return graph.invoke(initial_state)

    if langfuse:
        with langfuse.start_as_current_span(
            name="reconcile_transaction",
            input={
                "transaction_id": transaction.id,
                "counterparty": transaction.counterparty_name,
                "amount": transaction.amount,
                "date": transaction.date.isoformat(),
            },
        ) as root_span:
            langfuse.update_current_trace(
                name=f"reconcile:{transaction.counterparty_name}",
                metadata={"currency": transaction.currency},
            )
            final_state = _run()

            proposal = final_state.get("match_proposal")
            error = final_state.get("error")
            status = proposal.status.value if proposal else ("error" if error else "no_match")

            root_span.update(
                output={
                    "status": status,
                    "confidence": proposal.confidence_score if proposal else None,
                    "emails_found": final_state.get("emails_found", 0),
                    "ocr_attempts": final_state.get("ocr_candidates_tried", 0),
                }
            )
    else:
        final_state = _run()
        proposal = final_state.get("match_proposal")
        error = final_state.get("error")
        status = proposal.status.value if proposal else ("error" if error else "no_match")

    result = ReconciliationResult(
        transaction_id=transaction.id,
        status=status,
        match_proposal=proposal,
        matched_email=final_state.get("best_email_invoice"),
        gmail_query_used=final_state.get("gmail_query"),
        emails_found=final_state.get("emails_found", 0),
        error=error,
    )

    logger.info(
        f"Transaction {transaction.id} ({transaction.counterparty_name}): "
        f"status={result.status}, "
        f"confidence={proposal.confidence_score if proposal else 'N/A'}, "
        f"ocr_attempts={final_state.get('ocr_candidates_tried', 0)}"
    )

    if result.status == "matched":
        paid = _get_paid()
        if paid:
            try:
                paid.signals.create_signals(signals=[{
                    "event_name": "transaction_reconciled",
                    "customer": {"external_customer_id": transaction.customer_id},
                    "attribution": {"external_product_id": config.PAID_PRODUCT_ID},
                    "idempotency_key": f"reconcile_{transaction.id}",
                }])
            except Exception as e:
                logger.warning(f"PAID signal failed for txn {transaction.id}: {e}")

    return result


def reconcile_batch(transactions: list[Transaction]) -> list[ReconciliationResult]:
    """Reconcile a batch of transactions sequentially."""
    results = []
    for i, txn in enumerate(transactions):
        logger.info(f"--- Reconciling {i+1}/{len(transactions)}: {txn.counterparty_name} ---")
        result = reconcile_transaction(txn)
        results.append(result)

    matched = sum(1 for r in results if r.status == "matched")
    review = sum(1 for r in results if r.status == "needs_review")
    no_match = sum(1 for r in results if r.status == "no_match")
    errors = sum(1 for r in results if r.status == "error")

    logger.info(
        f"\n=== Batch complete: {len(results)} transactions ===\n"
        f"  Matched:      {matched}\n"
        f"  Needs review: {review}\n"
        f"  No match:     {no_match}\n"
        f"  Errors:       {errors}"
    )

    langfuse = _get_langfuse()
    if langfuse:
        langfuse.flush()

    return results
