"""Generate Gmail search queries from transaction data using an LLM.

The LLM gets the transaction fields and produces a structured Gmail search query
optimised for finding the matching invoice email.

Two public functions:
- build_search_query()        — primary query (specific, uses from: filter)
- build_broad_fallback_query()— wider query used when the primary returns 0 results
"""

import json
import logging
import re

import litellm

import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Gmail search query generator for an invoice reconciliation tool.

Given a bank transaction, generate a Gmail search query to find the email containing
the matching invoice or receipt PDF.

Rules for Gmail search syntax:
- ALWAYS include has:attachment and filename:pdf
- Use "from:" to filter by the vendor's likely email domain when you can infer it
  e.g. for "Stripe" use from:stripe.com, for "Amazon Web Services" use from:amazon.com
  If you cannot confidently infer the domain, omit the from: filter
- Use "after:" and "before:" for a date range (format: YYYY/MM/DD)
  The range should cover 30 days before the transaction date up to the transaction date
- Use 1-2 keywords from the vendor name only if there is no reliable from: filter
- Keep the query broad enough to catch the email — too specific risks missing it
- Do NOT use quotes around the from: value

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
- Reference: {reference}

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
        return _deterministic_query(transaction_date, counterparty_name)
    except Exception as e:
        logger.error(f"LLM search query generation failed: {e}")
        return _deterministic_query(transaction_date, counterparty_name)


def build_broad_fallback_query(counterparty_name: str) -> dict:
    """Generate a wider fallback query when the primary query returns 0 results.

    Drops the date filter and the from: constraint, keeping only the vendor
    keywords and attachment filter so we cast a wider net.
    """
    key_words = _key_name_words(counterparty_name, max_words=1)
    name_query = key_words[0] if key_words else counterparty_name.split()[0]

    query = f"{name_query} has:attachment filename:pdf"

    logger.info(f"Broad fallback query for '{counterparty_name}': {query}")
    return {
        "query": query,
        "reasoning": "Broad fallback: no date range, no from: filter — wider net",
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Words to strip from company names when building keyword queries
_STOP_WORDS = {
    # English entity suffixes
    "llc", "ltd", "limited", "inc", "incorporated", "corp", "corporation",
    "plc", "llp", "lp", "co", "company", "group", "holdings", "international",
    # German entity suffixes
    "gmbh", "ag", "kg", "ohg", "ug", "mbh",
    # Filler
    "the", "and", "&", "of", "for",
}


def _key_name_words(name: str, max_words: int = 2) -> list[str]:
    """Extract the most meaningful words from a company name."""
    tokens = re.findall(r"[a-zA-Z0-9]+", name)
    meaningful = [w for w in tokens if w.lower() not in _STOP_WORDS and len(w) > 1]
    return meaningful[:max_words]


def _deterministic_query(transaction_date: str, counterparty_name: str) -> dict:
    """Deterministic fallback if LLM fails."""
    from datetime import datetime, timedelta

    txn_date = datetime.strptime(transaction_date, "%Y-%m-%d")
    after_date = (txn_date - timedelta(days=30)).strftime("%Y/%m/%d")
    before_date = (txn_date + timedelta(days=1)).strftime("%Y/%m/%d")

    key_words = _key_name_words(counterparty_name, max_words=2)
    name_query = " ".join(key_words) if key_words else counterparty_name.split()[0]

    query = f"{name_query} has:attachment filename:pdf after:{after_date} before:{before_date}"

    return {
        "query": query,
        "reasoning": "Deterministic fallback: vendor keywords + date range",
    }
