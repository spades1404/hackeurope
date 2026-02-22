"""Gmail API integration: search for emails and download PDF attachments.

Handles OAuth2 authentication, email metadata scanning, and deferred PDF download.

Flow:
1. find_invoice_candidates()  — searches Gmail, fetches metadata for all results
                                 (no PDF content downloaded yet)
2. Caller scores candidates via pre_filter_score() (in matching_engine)
3. download_pdf_for_candidate() — downloads PDF only for the chosen candidate
"""

import base64
import logging
import os
import re
from datetime import date, datetime

from schemas import EmailCandidate, EmailInvoice
import config

logger = logging.getLogger(__name__)


class GmailService:
    """Searches Gmail and extracts PDF attachments."""

    def __init__(self):
        self.service = None

    def authenticate(self):
        """Authenticate with Gmail API using OAuth2 credentials."""
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
        creds = None

        if os.path.exists(config.GMAIL_TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(config.GMAIL_TOKEN_PATH, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(config.GMAIL_CREDENTIALS_PATH):
                    raise FileNotFoundError(
                        f"Gmail credentials not found at {config.GMAIL_CREDENTIALS_PATH}. "
                        "Download from Google Cloud Console → APIs & Services → Credentials."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.GMAIL_CREDENTIALS_PATH, SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(config.GMAIL_TOKEN_PATH, "w") as token:
                token.write(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail API authenticated")

    def _ensure_authenticated(self):
        if not self.service:
            self.authenticate()

    def search_emails(self, query: str, max_results: int = 10) -> list[dict]:
        """Search Gmail and return message ID list (no content fetched).

        Args:
            query: Gmail search query string
            max_results: Max emails to return

        Returns:
            List of message dicts with 'id' and 'threadId'
        """
        self._ensure_authenticated()

        results = (
            self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )

        messages = results.get("messages", [])
        logger.info(f"Gmail search '{query}' → {len(messages)} results")
        return messages

    def get_email_metadata(self, message_id: str) -> EmailCandidate | None:
        """Fetch email headers and check for PDF presence — no attachment download.

        Uses format='full' to get the full MIME structure so we can detect PDF
        attachments and store their attachment IDs for deferred download.
        Inline (small) PDFs are stored directly in the candidate so no second
        fetch is needed later.

        Args:
            message_id: Gmail message ID

        Returns:
            EmailCandidate with metadata and PDF info, or None on error
        """
        self._ensure_authenticated()

        try:
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
        except Exception as e:
            logger.warning(f"Failed to fetch metadata for message {message_id}: {e}")
            return None

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        email_from = headers.get("From", "")
        email_subject = headers.get("Subject", "")
        email_date_str = headers.get("Date", "")
        email_date = _parse_email_date(email_date_str)

        # Scan MIME structure for a PDF — store IDs but don't download yet
        pdf_info = _scan_for_pdf(msg["payload"])

        body_text = _extract_body_text(msg["payload"])
        invoice_date_hint = _parse_invoice_date(body_text)

        return EmailCandidate(
            email_id=message_id,
            email_from=email_from,
            email_subject=email_subject,
            email_date=email_date,
            has_pdf=pdf_info is not None,
            pdf_filename=pdf_info[0] if pdf_info else None,
            pdf_attachment_id=pdf_info[1] if pdf_info else None,
            pdf_inline_data=pdf_info[2] if pdf_info else None,
            invoice_date_hint=invoice_date_hint,
        )

    def download_pdf_for_candidate(self, candidate: EmailCandidate) -> EmailInvoice | None:
        """Download the PDF for a pre-screened candidate.

        If the PDF was small enough to be stored inline in the metadata scan,
        no additional API call is made.  Otherwise, calls attachments.get().

        Args:
            candidate: An EmailCandidate returned by get_email_metadata()

        Returns:
            EmailInvoice with pdf_base64 populated, or None if PDF unavailable
        """
        if not candidate.has_pdf:
            logger.debug(f"Candidate {candidate.email_id} has no PDF — skipping download")
            return None

        self._ensure_authenticated()

        if candidate.pdf_inline_data:
            # Already available from the metadata scan — no extra API call
            pdf_base64 = candidate.pdf_inline_data
        elif candidate.pdf_attachment_id:
            try:
                attachment = (
                    self.service.users()
                    .messages()
                    .attachments()
                    .get(
                        userId="me",
                        messageId=candidate.email_id,
                        id=candidate.pdf_attachment_id,
                    )
                    .execute()
                )
                raw_b64 = attachment["data"]
                pdf_base64 = raw_b64.replace("-", "+").replace("_", "/")
            except Exception as e:
                logger.warning(
                    f"Failed to download attachment for {candidate.email_id}: {e}"
                )
                return None
        else:
            logger.warning(
                f"Candidate {candidate.email_id} has_pdf=True but no attachment_id or inline data"
            )
            return None

        return EmailInvoice(
            email_id=candidate.email_id,
            email_from=candidate.email_from,
            email_subject=candidate.email_subject,
            email_date=candidate.email_date,
            filename=candidate.pdf_filename or "invoice.pdf",
            pdf_base64=pdf_base64,
        )

    def find_invoice_candidates(
        self, query: str, max_results: int | None = None
    ) -> list[EmailCandidate]:
        """Search Gmail and return metadata for all matching emails.

        This is the main entry point used by the reconciliation agent.
        No PDFs are downloaded — callers should score candidates first, then
        call download_pdf_for_candidate() only for promising ones.

        Args:
            query: Gmail search query
            max_results: Override config.MAX_SEARCH_RESULTS

        Returns:
            List of EmailCandidate objects, ordered by Gmail relevance rank.
            Candidates without a PDF attachment are included (with has_pdf=False)
            so callers have full visibility, but they will score low.
        """
        n = max_results or config.MAX_SEARCH_RESULTS
        messages = self.search_emails(query, max_results=n)

        candidates = []
        for msg_meta in messages:
            candidate = self.get_email_metadata(msg_meta["id"])
            if candidate:
                candidates.append(candidate)

        pdf_count = sum(1 for c in candidates if c.has_pdf)
        logger.info(
            f"Metadata scan complete: {len(candidates)} emails, {pdf_count} with PDF"
        )
        return candidates


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _scan_for_pdf(
    payload: dict,
) -> tuple[str, str | None, str | None] | None:
    """Recursively scan MIME parts for a PDF attachment.

    Returns (filename, attachment_id_or_None, inline_base64_or_None),
    or None if no PDF found.

    attachment_id is set for large attachments that need a separate download.
    inline_base64 is set for small attachments already embedded in the message.
    Gmail URL-safe base64 is converted to standard base64 for inline data.
    """
    parts = payload.get("parts", [])

    if not parts:
        # Single-part message — check the payload itself
        filename = payload.get("filename", "")
        if filename.lower().endswith(".pdf"):
            body = payload.get("body", {})
            attachment_id = body.get("attachmentId")
            if attachment_id:
                return filename, attachment_id, None
            inline_data = body.get("data")
            if inline_data:
                return filename, None, inline_data.replace("-", "+").replace("_", "/")
        return None

    # Multipart message — check direct children, then recurse into nested multiparts
    for part in parts:
        filename = part.get("filename", "")
        if filename.lower().endswith(".pdf"):
            body = part.get("body", {})
            attachment_id = body.get("attachmentId")
            if attachment_id:
                return filename, attachment_id, None
            inline_data = body.get("data")
            if inline_data:
                return filename, None, inline_data.replace("-", "+").replace("_", "/")

        if part.get("parts"):
            result = _scan_for_pdf(part)
            if result:
                return result

    return None


def _extract_body_text(payload: dict) -> str:
    """Recursively extract plain text (or HTML stripped of tags) from MIME payload."""
    mime_type = payload.get("mimeType", "")
    parts = payload.get("parts", [])

    if not parts:
        if mime_type in ("text/plain", "text/html"):
            data = payload.get("body", {}).get("data", "")
            if data:
                raw = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
                if mime_type == "text/html":
                    raw = re.sub(r"<[^>]+>", " ", raw)
                return raw
        return ""

    # Prefer text/plain parts, fall back to text/html
    plain, html = "", ""
    for part in parts:
        ptype = part.get("mimeType", "")
        if ptype == "text/plain":
            plain += _extract_body_text(part)
        elif ptype == "text/html":
            html += _extract_body_text(part)
        elif ptype.startswith("multipart/"):
            plain += _extract_body_text(part)

    return plain or html


# Date patterns to look for in the email body, paired with strptime format strings
_DATE_PATTERNS = [
    # "Invoice Date: 2023-01-15" or "Date: 2023-01-15"
    (r"(?:invoice\s+date|billing\s+date|date)[:\s]+(\d{4}-\d{2}-\d{2})", "%Y-%m-%d"),
    # "Invoice Date: 15/01/2023"
    (r"(?:invoice\s+date|billing\s+date|date)[:\s]+(\d{2}/\d{2}/\d{4})", "%d/%m/%Y"),
    # "Invoice Date: January 15, 2023"
    (r"(?:invoice\s+date|billing\s+date|date)[:\s]+([A-Za-z]+ \d{1,2},? \d{4})", "%B %d %Y"),
    # "Invoice Date: 15 January 2023"
    (r"(?:invoice\s+date|billing\s+date|date)[:\s]+(\d{1,2} [A-Za-z]+ \d{4})", "%d %B %Y"),
    # Bare ISO date anywhere in the body as last resort
    (r"\b(\d{4}-\d{2}-\d{2})\b", "%Y-%m-%d"),
]


def _parse_invoice_date(body_text: str) -> date | None:
    """Extract the most likely invoice date from email body text."""
    if not body_text:
        return None
    text = body_text.lower()
    for pattern, fmt in _DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1).strip().rstrip(",")
            # Normalise "january 5 2023" → "January 05 2023" for strptime
            raw = re.sub(r"\s+", " ", raw)
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
    return None


def _parse_email_date(date_str: str) -> datetime:
    """Parse Gmail date header into datetime.

    Strips parenthetical timezone comments like '(PST)' or '(UTC)' that
    Gmail occasionally appends after the numeric offset.
    """
    import re
    # Remove trailing parenthetical e.g. " (PST)", " (UTC+1)"
    cleaned = re.sub(r"\s*\([^)]*\)\s*$", "", date_str.strip())

    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue

    logger.warning(f"Could not parse email date: {date_str!r}")
    return datetime.now()
