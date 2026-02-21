"""Generate Gmail search queries from transaction data using an LLM.

The LLM gets the transaction fields and produces a structured Gmail search query
optimized for finding the matching invoice email.
"""

import json
import logging

import litellm

import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Gmail search query generator for a German tax advisory tool.

Given a bank transaction, you generate a Gmail search query to find the email 
containing the matching invoice PDF.

Rules for Gmail search syntax:
- Use "from:" to filter by sender (if you can infer the vendor's email domain)
- Use "has:attachment" to ensure PDF attachments
- Use "filename:pdf" to filter for PDF files
- Use "after:" and "before:" for date range (format: YYYY/MM/DD)
- Use keywords from the vendor name (but keep it simple — 1-2 key words)
- Do NOT use quotes around multi-word "from:" values
- Keep queries short and broad enough to catch the email — too specific risks missing it

The date range should cover from 30 days before the transaction date to the transaction date,
since invoices are typically sent before payment.

Return ONLY a JSON object with this exact structure, no markdown:
{
    "query": "the Gmail search query string",
    "reasoning": "brief explanation of query construction"
}"""

USER_PROMPT_TEMPLATE = """Generate a Gmail search query for this bank transaction:

- Date: {date}
- Amount: {amount} {currency}
- Counterparty: {counterparty_name}
- IBAN: {iban}
- Reference (Verwendungszweck): {reference}

Return the JSON object with the query."""


def build_search_query(
    transaction_date: str,
    amount: float,
    currency: str,
    counterparty_name: str,
    iban: str | None = None,
    reference: str | None = None,
    model: str | None = None,
) -> dict:
    """Use an LLM to generate a Gmail search query for a transaction.

    Returns:
        dict with "query" and "reasoning" keys
    """
    model = model or config.SEARCH_QUERY_MODEL

    user_prompt = USER_PROMPT_TEMPLATE.format(
        date=transaction_date,
        amount=abs(amount),
        currency=currency,
        counterparty_name=counterparty_name,
        iban=iban or "N/A",
        reference=reference or "N/A",
    )

    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=300,
        )

        raw = response.choices[0].message.content.strip()

        # Clean markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

        result = json.loads(raw)
        logger.info(f"Search query for '{counterparty_name}': {result['query']}")
        return result

    except json.JSONDecodeError as e:
        logger.warning(f"LLM returned invalid JSON, falling back to deterministic query: {e}")
        return _fallback_query(transaction_date, counterparty_name)
    except Exception as e:
        logger.error(f"LLM search query generation failed: {e}")
        return _fallback_query(transaction_date, counterparty_name)


def _fallback_query(transaction_date: str, counterparty_name: str) -> dict:
    """Deterministic fallback if LLM fails."""
    from datetime import datetime, timedelta

    txn_date = datetime.strptime(transaction_date, "%Y-%m-%d")
    after_date = (txn_date - timedelta(days=30)).strftime("%Y/%m/%d")
    before_date = (txn_date + timedelta(days=1)).strftime("%Y/%m/%d")

    # Take first meaningful word from counterparty name
    words = counterparty_name.split()
    stop_words = {"gmbh", "ag", "kg", "ohg", "ug", "e.k.", "mbh", "co.", "&", "und", "the"}
    key_words = [w for w in words if w.lower().strip(".,") not in stop_words][:2]
    name_query = " ".join(key_words) if key_words else counterparty_name.split()[0]

    query = f"{name_query} has:attachment filename:pdf after:{after_date} before:{before_date}"

    return {
        "query": query,
        "reasoning": "Fallback: deterministic query using vendor name keywords and date range",
    }
