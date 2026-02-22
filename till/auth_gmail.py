"""Run this once to authenticate with Gmail and generate token.json.

Prerequisites:
- credentials.json in the same directory (from Google Cloud Console)
- Be logged into the target Gmail account in your default browser

Usage:
    pip install google-auth-oauthlib google-api-python-client
    python auth_gmail.py
"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH = "token.json"


def main():
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"ERROR: {CREDENTIALS_PATH} not found in current directory.")
        print("Download it from Google Cloud Console → APIs & Services → Credentials")
        return

    print("Opening browser for Gmail authorization...")
    print("Make sure you're logged into the target Gmail account in your browser.\n")

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())

    print(f"\n✓ token.json saved successfully!")

    # Quick verification
    service = build("gmail", "v1", credentials=creds)
    profile = service.users().getProfile(userId="me").execute()
    print(f"✓ Authenticated as: {profile['emailAddress']}")
    print(f"✓ Total messages: {profile['messagesTotal']}")
    print(f"\nYou're all set. Place both credentials.json and token.json in your project root.")


if __name__ == "__main__":
    main()