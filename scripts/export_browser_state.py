"""
CareerOrbit - FR-18: Persistent Chrome Profile & Storage State Exporter
Allows the student to log in once to Google, LinkedIn, Internshala, Unstop, and Naukri.
Exports authenticated session cookies and local storage to ./storage/storage_state.json
so the 24/7 background agent stays logged in continuously without re-triggering bot detection.
"""

import sys
import os
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

# Add repo root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.config import settings

def export_browser_state(headless: bool = False, non_interactive: bool = False):
    """
    Spawns Chromium with the persistent user profile directory and saves storage_state.json.
    """
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    settings.CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 65)
    print("  CareerOrbit: Persistent Browser Authentication Manager")
    print("=" * 65)
    print(f"Profile Directory: {settings.CHROME_PROFILE_DIR}")
    print(f"Target Output:    {settings.STORAGE_STATE_PATH}")
    print("=" * 65 + "\n")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(settings.CHROME_PROFILE_DIR),
            headless=headless,
            viewport={"width": 1280, "height": 800},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        
        page = context.pages[0] if context.pages else context.new_page()

        if non_interactive:
            # Used for CI / automated verification
            print("[INFO] Running in non-interactive mode. Generating valid baseline state...")
            page.goto("data:text/html,<html><head><title>CareerOrbit Session</title></head><body><h1>CareerOrbit Session Initialized</h1></body></html>")
            context.storage_state(path=str(settings.STORAGE_STATE_PATH))
            context.close()
            print(f"[SUCCESS] Staged session state written to {settings.STORAGE_STATE_PATH}")
            return str(settings.STORAGE_STATE_PATH)

        print("\nPortal quick-links to log in:")
        print(" 1. Google (OAuth):    https://accounts.google.com")
        print(" 2. LinkedIn:          https://www.linkedin.com/login")
        print(" 3. Internshala:       https://internshala.com/login/student")
        print(" 4. Unstop:            https://unstop.com/auth/login")
        print(" 5. Naukri:            https://www.naukri.com/nlogin/login")
        print("\nNavigating to Google Sign-in to start...")
        
        try:
            page.goto("https://accounts.google.com", timeout=60000)
        except Exception as e:
            print(f"[NOTE] Initial navigation: {e}")

        print("\n" + "*" * 65)
        print(" ACTION REQUIRED:")
        print(" Complete your logins in the browser window.")
        print(" When finished, return here and press [ENTER] to save your authenticated state.")
        print("*" * 65 + "\n")

        try:
            input("Press [ENTER] to capture storage state and exit... ")
        except (EOFError, KeyboardInterrupt):
            pass

        # Save session cookies & local storage
        context.storage_state(path=str(settings.STORAGE_STATE_PATH))
        context.close()
        print(f"\n[SUCCESS] Authenticated storage state saved to {settings.STORAGE_STATE_PATH}")
        return str(settings.STORAGE_STATE_PATH)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export authenticated browser state for CareerOrbit 24/7 Agent.")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode.")
    parser.add_argument("--test", action="store_true", help="Non-interactive test mode for automated verification.")
    args = parser.parse_args()

    export_browser_state(headless=args.headless or args.test, non_interactive=args.test)
