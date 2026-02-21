"""Gmail API integration: search for emails and download PDF attachments.

Handles OAuth2 authentication, email search, and PDF extraction.
"""

import base64
import logging
import os
from datetime import datetime

from models.schemas import EmailInvoice
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

    def search_emails(self, query: str, max_results: int = 5) -> list[dict]:
        """Search Gmail and return message metadata.

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

    def get_email_with_pdf(self, message_id: str) -> EmailInvoice | None:
        """Fetch a single email and extract the first PDF attachment.

        Args:
            message_id: Gmail message ID

        Returns:
            EmailInvoice with PDF base64 data, or None if no PDF found
        """
        self._ensure_authenticated()

        msg = (
            self.service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

        # Extract headers
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        email_from = headers.get("From", "")
        email_subject = headers.get("Subject", "")
        email_date_str = headers.get("Date", "")

        # Parse date (Gmail dates vary in format)
        email_date = _parse_email_date(email_date_str)

        # Find PDF attachment in message parts
        pdf_data = self._find_pdf_attachment(msg["payload"], message_id)

        if not pdf_data:
            logger.debug(f"No PDF attachment in email {message_id}")
            return None

        filename, pdf_base64 = pdf_data

        return EmailInvoice(
            email_id=message_id,
            email_from=email_from,
            email_subject=email_subject,
            email_date=email_date,
            filename=filename,
            pdf_base64=pdf_base64,
        )

    def _find_pdf_attachment(self, payload: dict, message_id: str) -> tuple[str, str] | None:
        """Recursively search message parts for a PDF attachment.

        Returns (filename, base64_data) or None.
        """
        parts = payload.get("parts", [])

        # Also check the payload itself (for single-part messages)
        parts_to_check = [payload] + parts

        for part in parts_to_check:
            filename = part.get("filename", "")

            if filename.lower().endswith(".pdf"):
                attachment_id = part.get("body", {}).get("attachmentId")

                if attachment_id:
                    # Download attachment data
                    attachment = (
                        self.service.users()
                        .messages()
                        .attachments()
                        .get(userId="me", messageId=message_id, id=attachment_id)
                        .execute()
                    )
                    # Gmail uses URL-safe base64 — convert to standard
                    raw_b64 = attachment["data"]
                    raw_b64 = raw_b64.replace("-", "+").replace("_", "/")
                    return filename, raw_b64

                elif part.get("body", {}).get("data"):
                    # Small attachments might be inline
                    raw_b64 = part["body"]["data"]
                    raw_b64 = raw_b64.replace("-", "+").replace("_", "/")
                    return filename, raw_b64

            # Recurse into nested parts (multipart messages)
            if part.get("parts"):
                result = self._find_pdf_attachment(part, message_id)
                if result:
                    return result

        return None

    def find_invoice_email(self, query: str) -> EmailInvoice | None:
        """Search Gmail and return the top matching email with a PDF attachment.

        This is the main method used by the reconciliation agent.
        Searches, then iterates results until one with a PDF is found.
        """
        messages = self.search_emails(query, max_results=5)

        for msg_meta in messages:
            invoice_email = self.get_email_with_pdf(msg_meta["id"])
            if invoice_email:
                return invoice_email

        logger.info(f"No email with PDF found for query: {query}")
        return None


def _parse_email_date(date_str: str) -> datetime:
    """Parse Gmail date header into datetime."""
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue

    logger.warning(f"Could not parse email date: {date_str}")
    return datetime.now()
