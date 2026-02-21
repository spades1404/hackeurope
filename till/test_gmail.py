"""Quick test: verify Gmail API access and list recent emails with PDF attachments."""

import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = "token.json"


def main():
    if not os.path.exists(TOKEN_PATH):
        print("ERROR: token.json not found. Run auth_gmail.py first.")
        return

    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    service = build("gmail", "v1", credentials=creds)

    # 1. Profile check
    profile = service.users().getProfile(userId="me").execute()
    print(f"✓ Connected as: {profile['emailAddress']}")
    print(f"  Total messages: {profile['messagesTotal']}\n")

    # 2. List 5 most recent emails
    print("--- 5 Most Recent Emails ---")
    results = service.users().messages().list(userId="me", maxResults=5).execute()
    messages = results.get("messages", [])

    for msg_meta in messages:
        msg = service.users().messages().get(userId="me", id=msg_meta["id"], format="full").execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        print(f"  From: {headers.get('From', '?')}")
        print(f"  Subject: {headers.get('Subject', '?')}")
        print(f"  Date: {headers.get('Date', '?')}")
        print()

    # 3. Search for emails with PDF attachments
    print("--- Emails with PDF Attachments ---")
    results = service.users().messages().list(
        userId="me", q="has:attachment filename:pdf", maxResults=10
    ).execute()
    pdf_messages = results.get("messages", [])
    print(f"  Found: {len(pdf_messages)} emails with PDFs\n")

    for msg_meta in pdf_messages[:5]:
        msg = service.users().messages().get(userId="me", id=msg_meta["id"], format="full").execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        print(f"  From: {headers.get('From', '?')}")
        print(f"  Subject: {headers.get('Subject', '?')}")

        # Find PDF filenames
        parts = msg["payload"].get("parts", [])
        for part in parts:
            filename = part.get("filename", "")
            if filename.lower().endswith(".pdf"):
                size = part.get("body", {}).get("size", 0)
                print(f"    📎 {filename} ({size} bytes)")
        print()


if __name__ == "__main__":
    main()