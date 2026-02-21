"""Data models for invoice reconciliation."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from enum import Enum


class MatchStatus(str, Enum):
    PENDING = "pending"
    MATCHED = "matched"
    REJECTED = "rejected"
    NO_MATCH = "no_match"
    NEEDS_REVIEW = "needs_review"


class Transaction(BaseModel):
    """A bank transaction to reconcile."""
    id: str
    date: date
    amount: float  # negative = outgoing, positive = incoming
    currency: str = "EUR"
    counterparty_name: str
    counterparty_iban: Optional[str] = None
    reference: Optional[str] = None  # Verwendungszweck
    match_status: MatchStatus = MatchStatus.PENDING


class ExtractedInvoiceData(BaseModel):
    """Structured data extracted from an invoice PDF via OCR."""
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_tax_id: Optional[str] = None  # USt-IdNr
    vendor_iban: Optional[str] = None
    buyer_name: Optional[str] = None
    net_amount: Optional[float] = None
    vat_rate: Optional[float] = None
    vat_amount: Optional[float] = None
    gross_amount: Optional[float] = None
    line_items: list[dict] = Field(default_factory=list)
    payment_reference: Optional[str] = None  # Verwendungszweck


class EmailCandidate(BaseModel):
    """Email metadata scanned before PDF download — used for pre-filtering."""
    email_id: str
    email_from: str
    email_subject: str
    email_date: datetime
    has_pdf: bool = False
    pdf_filename: Optional[str] = None
    # Stored for later download (mutually exclusive):
    pdf_attachment_id: Optional[str] = None   # large attachment — needs attachments.get()
    pdf_inline_data: Optional[str] = None     # small inline attachment — already available
    # Set after pre-filter scoring:
    pre_filter_score: float = 0.0
    pre_filter_reasons: list[str] = Field(default_factory=list)


class EmailInvoice(BaseModel):
    """An invoice fetched from Gmail."""
    email_id: str
    email_from: str
    email_subject: str
    email_date: datetime
    filename: str
    pdf_base64: str  # standard base64-encoded PDF content
    extracted_data: Optional[ExtractedInvoiceData] = None


class MatchProposal(BaseModel):
    """A proposed match between a transaction and an invoice."""
    id: str
    transaction_id: str
    email_id: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    match_reasons: list[str] = Field(default_factory=list)
    amount_match: bool = False
    date_match: bool = False
    vendor_match: bool = False
    reference_match: bool = False
    iban_match: bool = False
    status: MatchStatus = MatchStatus.PENDING
    extracted_invoice: Optional[ExtractedInvoiceData] = None


class ReconciliationResult(BaseModel):
    """Result for a single transaction reconciliation."""
    transaction_id: str
    status: str  # "matched", "needs_review", "no_match", "error"
    match_proposal: Optional[MatchProposal] = None
    matched_email: Optional[EmailInvoice] = None  # email + PDF that produced the match
    gmail_query_used: Optional[str] = None
    emails_found: int = 0
    error: Optional[str] = None
