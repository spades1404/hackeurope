"""Test PDF download + vision model extraction on the most recent email with a PDF."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from gmail_service import GmailService
from invoice_extractor import extract_invoice_data


def main():
    print("Authenticating with Gmail...")
    gmail = GmailService()
    gmail.authenticate()

    print("Searching for most recent email with a PDF attachment...")
    # Broad query — just find the latest email with any PDF
    messages = gmail.search_emails("has:attachment filename:pdf", max_results=1)

    if not messages:
        print("No emails with PDF attachments found.")
        return

    msg_id = messages[0]["id"]
    print(f"Found message: {msg_id}")

    print("Fetching metadata...")
    candidate = gmail.get_email_metadata(msg_id)
    if not candidate:
        print("Failed to fetch metadata.")
        return

    print(f"  From:    {candidate.email_from}")
    print(f"  Subject: {candidate.email_subject}")
    print(f"  Date:    {candidate.email_date}")
    print(f"  PDF:     {candidate.pdf_filename} (has_pdf={candidate.has_pdf})")

    if not candidate.has_pdf:
        print("No PDF found in this email.")
        return

    print("\nDownloading PDF...")
    email_invoice = gmail.download_pdf_for_candidate(candidate)
    if not email_invoice:
        print("Failed to download PDF.")
        return

    pdf_size_kb = len(email_invoice.pdf_base64) * 3 / 4 / 1024  # approx bytes from base64
    print(f"Downloaded: {email_invoice.filename} (~{pdf_size_kb:.1f} KB)")

    print("\nRunning vision model extraction...")
    extracted = extract_invoice_data(email_invoice.pdf_base64)

    print("\n--- Extracted Invoice Data ---")
    print(json.dumps(extracted.model_dump(), indent=2, default=str))


if __name__ == "__main__":
    main()
