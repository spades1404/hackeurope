# Invoice Reconciliation Agent

Agentic invoice-to-transaction matching. Per transaction, the agent searches Gmail for the matching invoice email, extracts structured data from the PDF, and scores the match.

## Architecture

```
For each transaction:

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│  1. Generate │     │  2. Search   │     │  3. Extract  │     │ 4. Score │
│  Gmail Query │────▶│  Gmail + Get │────▶│  Invoice PDF │────▶│  Match   │
│  (LLM)       │     │  Top PDF     │     │  (Vision LLM)│     │ (Determ.)|
└──────────────┘     └──────────────┘     └──────────────┘     └──────────┘
   LiteLLM              Gmail API            LiteLLM           5 signals:
   (Gemini Flash)                            (Gemini Flash)    amount 40%
                                                               vendor 25%
                                                               date   15%
                                                               ref    10%
                                                               IBAN   10%
```

All steps traced in **Langfuse**.

## Setup

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Set GEMINI_API_KEY, Langfuse keys, Gmail OAuth path

# 3. Gmail OAuth
# - Create project in Google Cloud Console
# - Enable Gmail API
# - Create OAuth2 credentials (Desktop app)
# - Download as credentials.json into project root
# - First run will open browser for auth → creates token.json

# 4. Run
python main.py
# API docs: http://localhost:8001/docs
```

## API

### `POST /reconcile`

```json
{
  "transactions": [
    {
      "id": "txn-001",
      "date": "2025-01-15",
      "amount": -1190.00,
      "currency": "EUR",
      "counterparty_name": "Müller IT Solutions GmbH",
      "counterparty_iban": "DE89370400440532013000",
      "reference": "RE-2025-0042 IT Beratung"
    }
  ]
}
```

Response includes per-transaction match proposals with confidence scores and reasons.

### `POST /reconcile/feedback`

```json
{"transaction_id": "txn-001", "decision": "accept"}
```

### `GET /reconcile/{transaction_id}`

Get stored result for a specific transaction.

## Swapping Models

All LLM calls go through LiteLLM. Change models in `.env`:

```bash
# Use Claude for extraction instead
EXTRACTION_MODEL=anthropic/claude-sonnet-4-20250514

# Use GPT-4o for search queries
SEARCH_QUERY_MODEL=openai/gpt-4o
```

## Project Structure

```
invoice-reconciliation/
├── agents/
│   └── reconciliation_agent.py   # LangGraph workflow + Langfuse tracing
├── services/
│   ├── search_query_builder.py   # LLM generates Gmail search queries
│   ├── gmail_service.py          # Gmail API: search + PDF download
│   ├── invoice_extractor.py      # Vision LLM: PDF → structured data
│   └── matching_engine.py        # Deterministic multi-signal scorer
├── models/
│   └── schemas.py                # Pydantic models
├── config.py                     # LiteLLM model config + settings
├── main.py                       # FastAPI server
├── requirements.txt
└── .env.example
```
