"""
CareerClaw - FR-24 & FR-26: Google OAuth 2.0 Authorization Script
Authorizes Gmail (Read-Only) and Google Calendar (Events) APIs.
Saves persistent refresh token to ./storage/google_token.json so the 24/7 cloud daemon
can monitor recruiter emails and schedule OA focus blocks without ongoing interactive prompts.
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add repo root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.config import settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.events"
]

def authorize_google(test_mode: bool = False):
    """
    Executes OAuth2 flow using credentials.json and saves google_token.json.
    """
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    credentials_path = settings.BACKEND_DIR / "credentials.json"
    token_path = settings.STORAGE_DIR / "google_token.json"

    print("\n" + "=" * 65)
    print("  CareerClaw: Gmail & Google Calendar Authorization")
    print("=" * 65)
    print(f"Credentials File: {credentials_path}")
    print(f"Target Token:     {token_path}")
    print("=" * 65 + "\n")

    if test_mode:
        print("[INFO] Running in test mode. Creating mock token file for CI validation...")
        mock_token = {
            "token": "ya29.mock_token_for_ci_testing_careerclaw_2026",
            "refresh_token": "1//04mock_refresh_token_careerclaw_2026",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "mock_client_id.apps.googleusercontent.com",
            "client_secret": "mock_client_secret",
            "scopes": SCOPES,
            "expiry": "2030-01-01T00:00:00.000000Z"
        }
        with open(token_path, "w", encoding="utf-8") as f:
            json.dump(mock_token, f, indent=2)
        print(f"[SUCCESS] Test token written to {token_path}")
        return str(token_path)

    if not credentials_path.exists():
        print("[ERROR] backend/credentials.json not found!")
        print("Steps to obtain credentials:")
        print(" 1. Go to Google Cloud Console (https://console.cloud.google.com).")
        print(" 2. Enable 'Gmail API' and 'Google Calendar API'.")
        print(" 3. Go to 'Credentials' -> 'Create Credentials' -> 'OAuth client ID' (Desktop App).")
        print(f" 4. Download JSON and place at: {credentials_path}")
        return None

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)

        token_data = json.loads(creds.to_json())
        with open(token_path, "w", encoding="utf-8") as f:
            json.dump(token_data, f, indent=2)

        print(f"\n[SUCCESS] Permanent Google OAuth credentials saved to {token_path}!")
        print("The 24/7 daemon is now authorized to poll Gmail and schedule Calendar events.")
        return str(token_path)
    except Exception as e:
        print(f"[ERROR] OAuth flow failed: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Authorize CareerClaw with Google APIs.")
    parser.add_argument("--test", action="store_true", help="Generate mock token for automated verification.")
    args = parser.parse_args()

    authorize_google(test_mode=args.test)
