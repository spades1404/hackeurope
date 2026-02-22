# Invoice Reconciliation Agent — Technical Documentation

## 1. System Overview

The system is a **single-agent LangGraph workflow** — not a multi-agent hierarchy. One stateful graph handles the full reconciliation of each transaction, end to end. There is no agent-to-agent communication. The architecture is:

```
run_three.py / main.py
    └── reconcile_transaction(txn)         ← public API entry point
            └── LangGraph graph.invoke()
                    ├── Node 1: generate_query
                    ├── Node 2: search_gmail_metadata
                    ├── Node 3: pre_filter
                    └── Node 4: extract_until_confident
```

**External services called:**
- **Anthropic Claude** (via LiteLLM) — generates Gmail search queries
- **Google Gemini** (via LiteLLM) — OCR / vision extraction of invoice PDFs
- **Gmail API** (OAuth2) — email search and PDF download
- **Langfuse** — observability tracing

---

## 2. AgentState — The Shared Memory

`AgentState` is a `TypedDict` that flows through every node. Each node receives the full state and returns a partial dict of keys to update. LangGraph merges those updates into the state before calling the next node.

```
AgentState
├── transaction           Transaction          ← immutable input (bank transaction)
├── gmail_query           str | None           ← set by Node 1
├── gmail_query_reasoning str | None           ← set by Node 1 (LLM explanation)
├── email_candidates      list[EmailCandidate] ← set by Node 2 (unsorted, no PDFs)
├── ranked_candidates     list[EmailCandidate] ← set by Node 3 (sorted, scored)
├── best_email_invoice    EmailInvoice | None  ← set by Node 4 (winning email + PDF)
├── match_proposal        MatchProposal | None ← set by Node 4 (final match result)
├── emails_found          int                  ← count from Node 2
├── ocr_candidates_tried  int                  ← count from Node 4
└── error                 str | None           ← set on any fatal failure
```

The `Transaction` input object carries these fields from the bank statement:

```
id, date, amount (negative=outgoing), currency, counterparty_name,
counterparty_iban, reference (Verwendungszweck)
```

---

## 3. Step-by-Step: What Happens Each Run

### Node 1 — `generate_search_query`

**What it does:** Calls Claude (Haiku by default) to generate a Gmail search query from the transaction.

**Input used from state:** `transaction.counterparty_name`, `transaction.reference`, `transaction.amount`, `transaction.currency`, `transaction.date`

**LLM instruction:** The system prompt tells the model to:
- Always include `has:attachment filename:pdf`
- If a payment reference exists, use `subject:{reference}` — this is the strongest signal
- Include the most distinctive word from the vendor name as `subject:{vendor}`
- **Never** use `from:` filters or date range filters (emails come from varied addresses; synthetic data has all emails sent today)

**Example output:**
```
has:attachment filename:pdf subject:IE-202301-34922 subject:HubSpot
```

**Fallback:** If the LLM call fails or returns invalid JSON, `_deterministic_query()` builds the same structure deterministically from `reference` + first meaningful token of the vendor name.

**State updates:** `gmail_query`, `gmail_query_reasoning`

---

### Node 2 — `search_gmail_metadata`

**What it does:** Executes the Gmail search and fetches **metadata only** for all results — no PDFs are downloaded yet.

**Gmail call flow (per email):**
1. `messages.list(q=query, maxResults=10)` → list of `{id, threadId}`
2. For each message ID, `messages.get(format="full")` → full MIME structure + headers

**Per email, the metadata scan extracts:**
- `From`, `Subject`, `Date` headers
- Recursive MIME scan for a PDF attachment → stores `pdf_filename` + either `pdf_attachment_id` (large file, needs a second API call) or `pdf_inline_data` (small file, already present)
- **Invoice date hint:** plain text is extracted from the email body, then regex-matched against 5 date patterns to find the invoice date before any OCR:

  | Pattern | Format |
  |---|---|
  | `"Invoice Date: 2023-01-15"` | `%Y-%m-%d` |
  | `"Invoice Date: 15/01/2023"` | `%d/%m/%Y` |
  | `"January 15, 2023"` | `%B %d %Y` |
  | `"15 January 2023"` | `%d %B %Y` |
  | Bare ISO date anywhere in body | `%Y-%m-%d` (last resort) |

**Fallback query:** If the primary search returns 0 results, one automatic retry fires with a broader query: just `{vendor_keyword} has:attachment filename:pdf` — no subject filter, no date filter.

**State updates:** `email_candidates` (list of `EmailCandidate`), `emails_found`

---

### Node 3 — `pre_filter_candidates`

**What it does:** Scores every candidate on metadata alone (no PDFs, no OCR), then sorts the list to determine OCR priority order.

#### Pre-filter scoring (0.0–1.0)

Four signals, weighted:

| Signal | Weight | Logic |
|---|---|---|
| **Sender domain** | 50% | Extracts registered domain from `From` header (e.g. `billing@hubspot.com` → `hubspot`). Compares to vendor name tokens using `SequenceMatcher`. Exact token match → 1.0. |
| **Subject invoice keywords** | 20% | Binary: 1.0 if subject contains any of: `invoice`, `receipt`, `billing`, `statement`, `order confirmation`, `payment confirmation`, `subscription`, `renewal`, etc. |
| **Vendor name in subject** | 20% | Fraction of meaningful vendor name tokens found in subject. E.g. `HubSpot` in `"Invoice from HubSpot Ireland"` → 1.0. |
| **Date proximity** | 10% | Based on **email send date**. Scoring: 0–14 days before txn → 1.0 · 15–30 days → 0.8 · 31–60 days → 0.5 · up to 3 days after → 0.7 · otherwise → 0.1. |

**Hard rule:** Any candidate without a PDF attachment immediately gets score = 0.0 and is excluded from OCR.

#### Sort order

```python
ranked = sorted(scored, key=lambda c: (-c.pre_filter_score, _date_proximity(c)))
```

**Primary sort: pre-filter score descending** — a HubSpot email ranks above a Salesforce email for a HubSpot transaction.

**Tiebreaker: invoice date proximity ascending** — among candidates with identical scores (e.g. 6 monthly HubSpot invoices all from `billing@hubspot.com`), the one whose **invoice date hint** (extracted from the email body text) is closest to the transaction date is tried first via OCR. If no invoice date hint was extracted from the body, the email send date is used as a fallback.

#### Routing decision (after Node 3)

```python
def should_run_ocr(state):
    has_viable = any(
        c.has_pdf and c.pre_filter_score >= PRE_FILTER_MIN_SCORE  # default 0.15
        for c in ranked
    )
    return "continue" if has_viable else "no_match"
```

If no candidate clears the minimum threshold, the graph terminates immediately as `no_match` — no OCR is triggered.

---

### Node 4 — `extract_until_confident`

**What it does:** Iterates through `ranked_candidates` in order. For each candidate, runs the full OCR → match scoring pipeline. Stops early once a confident match is found.

#### Per-candidate loop

**Skip conditions (no OCR attempt counted):**
- `tried >= MAX_OCR_CANDIDATES` (default: 3) → hard stop
- `pre_filter_score < PRE_FILTER_MIN_SCORE` (default: 0.15) → stop processing rest
- `has_pdf == False` → skip silently

**For each viable candidate:**

**Step a — PDF download**
- If `pdf_inline_data` is set: reuse directly (no extra API call)
- If `pdf_attachment_id` is set: call `messages.attachments.get()` to download; convert Gmail URL-safe base64 to standard base64

**Step b — OCR extraction (Gemini vision)**

The full PDF is sent as `data:application/pdf;base64,...` to the Gemini model. The model is instructed to return only JSON with these fields:

```
invoice_number, invoice_date, due_date, vendor_name, vendor_address,
vendor_tax_id, vendor_iban, buyer_name, net_amount, vat_rate, vat_amount,
gross_amount, line_items, payment_reference
```

**Step c — Full match scoring**

Five signals against the bank transaction:

| Signal | Weight | Logic |
|---|---|---|
| **Amount** | 40% | Exact match → 1.0 · within 1% → 0.95 · matches net amount → 0.70 · within 5% → 0.50 · within 10% → 0.30 |
| **Vendor name** | 25% | Exact string → 1.0 · otherwise: max of fuzzy ratio, substring containment (≥0.85 if one name contains the other), word-level token overlap · `vendor_match = True` if ratio > 0.75 |
| **Date proximity** | 15% | 0 days → 1.0 · ≤14 days → 0.9 · ≤30 days → 0.7 · ≤60 days → 0.4 · txn before invoice → 0.1–0.5 |
| **Reference** | 10% | Invoice number found in transaction reference → 1.0 · fuzzy match of payment_reference → ratio |
| **IBAN** | 10% | Exact IBAN match (normalised, case-insensitive) → 1.0 |

**Confidence boost:** If `amount_match AND (vendor_match OR iban_match)` → confidence is floored at 0.90. This handles cases where the amount + identity are both confirmed but the other signals are weak.

**Status thresholds:**

```
confidence >= 0.85  → MATCHED
confidence >= 0.50  → NEEDS_REVIEW
confidence < 0.50   → NO_MATCH
```

**Early stop:** If any candidate reaches `confidence >= OCR_CONFIDENCE_TARGET` (default: 0.90), the loop breaks immediately — no further PDFs are downloaded.

The node always keeps track of the **best proposal seen so far** across all attempts, so even if the loop exhausts all 3 candidates without hitting the target, it returns the highest-confidence proposal found.

**State updates:** `match_proposal`, `best_email_invoice`, `ocr_candidates_tried`

---

## 4. Output Schema

The `reconcile_transaction()` function returns a `ReconciliationResult`:

```json
{
  "transaction_id": "TXN-20230105-001",
  "status": "matched",
  "gmail_query_used": "has:attachment filename:pdf subject:IE-202301-34922 subject:HubSpot",
  "emails_found": 4,
  "error": null,
  "match_proposal": {
    "id": "mp-TXN-20230105-001",
    "transaction_id": "TXN-20230105-001",
    "email_id": "18abc123def456",
    "confidence_score": 0.985,
    "status": "matched",
    "amount_match": true,
    "date_match": true,
    "vendor_match": true,
    "reference_match": true,
    "iban_match": false,
    "match_reasons": [
      "Exact amount: EUR2450.00",
      "Vendor match (94%): 'HubSpot Ireland Ltd' ↔ 'HubSpot Ireland'",
      "Date within 14 days: txn 2023-01-05 ← inv 2023-01-03",
      "Invoice number 'IE-202301-34922' found in reference"
    ],
    "extracted_invoice": {
      "invoice_number": "IE-202301-34922",
      "invoice_date": "2023-01-03",
      "due_date": "2023-01-31",
      "vendor_name": "HubSpot Ireland Ltd",
      "vendor_address": "2nd Floor 30 North Wall Quay, Dublin 1, Ireland",
      "vendor_tax_id": "IE9803175K",
      "vendor_iban": "IE29AIBK93115212345678",
      "buyer_name": "Tuna Tax Ltd",
      "net_amount": 2058.82,
      "vat_rate": 19.0,
      "vat_amount": 391.18,
      "gross_amount": 2450.00,
      "payment_reference": "IE-202301-34922",
      "line_items": [
        {
          "description": "HubSpot Marketing Hub Professional — Jan 2023",
          "quantity": 1,
          "unit_price": 2058.82,
          "total": 2058.82
        }
      ]
    }
  },
  "matched_email": {
    "email_id": "18abc123def456",
    "email_from": "billing@hubspot.com",
    "email_subject": "Invoice IE-202301-34922 from HubSpot Ireland — Tuna Tax Ltd",
    "email_date": "2023-01-03T09:14:22Z",
    "filename": "HubSpot_Invoice_IE-202301-34922.pdf",
    "pdf_base64": "<base64-encoded PDF content>"
  }
}
```

**Notes for consumers:**
- `status` is one of: `"matched"` | `"needs_review"` | `"no_match"` | `"error"`
- `match_proposal` and `matched_email` are `null` for `"no_match"` and `"error"` statuses
- `matched_email.pdf_base64` contains the raw PDF — can be rendered directly or stripped if only metadata is needed
- All amounts are plain numbers (no currency symbols), all dates are `YYYY-MM-DD`

---

## 5. Configuration Reference

All parameters are set via environment variables (`.env` file).

| Parameter | Default | Description |
|---|---|---|
| `EXTRACTION_MODEL` | `gemini/gemini-2.5-flash` | Vision model for PDF OCR |
| `SEARCH_QUERY_MODEL` | `anthropic/claude-haiku-4-5` | LLM for Gmail query generation |
| `MAX_SEARCH_RESULTS` | `10` | Max emails fetched per Gmail search |
| `MAX_OCR_CANDIDATES` | `3` | Max PDFs opened per transaction |
| `PRE_FILTER_MIN_SCORE` | `0.15` | Minimum pre-filter score to attempt OCR |
| `OCR_CONFIDENCE_TARGET` | `0.90` | Confidence at which OCR loop stops early |
| `CONFIDENCE_THRESHOLD_AUTO` | `0.85` | Score above which → `matched` |
| `CONFIDENCE_THRESHOLD_REVIEW` | `0.50` | Score above which → `needs_review` |
| `DATE_WINDOW_DAYS` | `30` | Max days between invoice and transaction to award date score |

---

## 6. Observability (Langfuse)

Each call to `reconcile_transaction()` creates one **trace** in Langfuse containing a tree of spans:

```
reconcile_transaction  (root span / trace)
├── generate_search_query        (span + generation: search_query_llm)
├── search_gmail_metadata        (span)
├── pre_filter_candidates        (span)
└── extract_until_confident      (span)
                                     └── invoice_extraction_llm  (generation, per PDF)
```

Token usage is reported on `generation` observations (not plain spans), which is why it appears in Langfuse's cost dashboard. Enable tracing by setting `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` in `.env`.
