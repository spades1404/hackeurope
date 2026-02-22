"""Invoice data extraction from PDF using LiteLLM (vision models).

Sends the PDF as a base64 document to a vision-capable model and extracts
structured invoice fields.
"""

import json
import logging

import litellm

import config
from schemas import ExtractedInvoiceData

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are an expert accountant. Analyze this invoice or receipt and
extract ALL fields into JSON.

Return ONLY valid JSON with this exact structure — no markdown, no explanation:

{
  "invoice_number": "invoice/receipt number as string",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD or null",
  "vendor_name": "seller/vendor company name",
  "vendor_address": "full address",
  "vendor_tax_id": "VAT number or tax ID if present",
  "vendor_iban": "IBAN if present",
  "buyer_name": "buyer company or person name",
  "net_amount": 0.00,
  "vat_rate": 0.0,
  "vat_amount": 0.00,
  "gross_amount": 0.00,
  "line_items": [{"description": "...", "quantity": 1, "unit_price": 0.00, "total": 0.00}],
  "payment_reference": "payment reference or memo if stated, else null"
}

Rules:
- All amounts as plain numbers, no currency symbols
- Dates strictly YYYY-MM-DD
- null for missing fields
- Common field labels to look for: Invoice No., Invoice #, Receipt No., Invoice Date,
  Issue Date, Due Date, Payment Due, Subtotal, Tax, VAT, GST, Total, Grand Total,
  Amount Due, Bill To, Sold To, Payment Reference, Memo, Order Number
- gross_amount = net_amount + vat_amount — verify the arithmetic"""


def extract_invoice_data(
    pdf_base64: str,
    model: str | None = None,
) -> ExtractedInvoiceData:
    """Extract structured data from a base64-encoded invoice PDF.

    Args:
        pdf_base64: Standard base64-encoded PDF content
        model: LiteLLM model string (defaults to config.EXTRACTION_MODEL)

    Returns:
        ExtractedInvoiceData with all available fields populated
    """
    model = model or config.EXTRACTION_MODEL

    # Build the message with inline PDF document
    # Gemini supports PDF via inline_data with application/pdf mime type
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:application/pdf;base64,{pdf_base64}",
                    },
                },
                {
                    "type": "text",
                    "text": EXTRACTION_PROMPT,
                },
            ],
        }
    ]

    try:
        try:
            from langfuse import get_client as _lf_client
            _lf = _lf_client()
        except Exception:
            _lf = None

        if _lf and _lf._tracing_enabled:
            gen_ctx = _lf.start_as_current_generation(
                name="invoice_extraction_llm",
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
                max_tokens=2000,
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

        data = json.loads(raw)
        result = ExtractedInvoiceData(**data)

        logger.info(
            f"Extracted invoice: vendor={result.vendor_name}, "
            f"amount=€{result.gross_amount}, nr={result.invoice_number}"
        )
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse extraction JSON: {e}\nRaw response: {raw}")
        raise ValueError(f"Model returned invalid JSON: {e}")
    except Exception as e:
        logger.error(f"Invoice extraction failed: {e}")
        raise
