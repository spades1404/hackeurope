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
- If a payment reference is provided, ALWAYS search for it in the subject line using
  subject:{reference} — the reference typically appears verbatim in the invoice subject
- Also include the most distinctive word from the vendor name with subject:
  e.g. for "HubSpot Ireland" add subject:HubSpot, for "Salesforce EMEA" add subject:Salesforce
  (skip generic words like Ireland, EMEA, Group, Ltd)
- Do NOT use from: filters or date range filters — invoice emails may come from
  various addresses and we rank by invoice date extracted from the body instead

Return ONLY a JSON object with this exact structure, no markdown:
{
    "query": "the Gmail search query string",
    "reasoning": "brief explanation of query construction"
}"""

USER_PROMPT_TEMPLATE = """Generate a Gmail search query for this bank transaction:

- Amount: {amount} {currency}
- Counterparty: {counterparty_name}
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
        amount=abs(amount),
        currency=currency,
        counterparty_name=counterparty_name,
        reference=reference or "N/A",
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        try:
            from langfuse import get_client as _lf_client
            _lf = _lf_client()
        except Exception:
            _lf = None

        if _lf and _lf._tracing_enabled:
            gen_ctx = _lf.start_as_current_generation(
                name="search_query_llm",
                model=model,
                input=messages,
            )
        else:
            from contextlib import nullcontext
            gen_ctx = nullcontext()

        with gen_ctx as gen:
            response = litellm.completion(
                model=model,
                messages=messages,
                temperature=0.0,
                max_tokens=300,
            )

            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()

            if gen is not None:
                usage = getattr(response, "usage", None)
                gen.update(
                    output=raw,
                    usage_details={
                        "input": getattr(usage, "prompt_tokens", 0),
                        "output": getattr(usage, "completion_tokens", 0),
                    },
                )

        result = json.loads(raw)
        logger.info(f"Search query for '{counterparty_name}': {result['query']}")
        return result

    except json.JSONDecodeError as e:
        logger.warning(f"LLM returned invalid JSON, falling back to deterministic query: {e}")
        return _deterministic_query(counterparty_name, reference)
    except Exception as e:
        logger.error(f"LLM search query generation failed: {e}")
        return _deterministic_query(counterparty_name, reference)


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


def _deterministic_query(counterparty_name: str, reference: str | None = None) -> dict:
    """Deterministic fallback if LLM fails."""
    key_words = _key_name_words(counterparty_name, max_words=1)
    name_query = key_words[0] if key_words else counterparty_name.split()[0]

    if reference:
        query = f"subject:{reference} subject:{name_query} has:attachment filename:pdf"
    else:
        query = f"subject:{name_query} has:attachment filename:pdf"

    return {
        "query": query,
        "reasoning": "Deterministic fallback: reference + vendor name in subject",
    }
