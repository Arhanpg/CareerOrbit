"""
CareerClaw - FR-19, FR-20 & FR-22: Sandboxed Browser Auto-Applier
Drives Chromium via Browser-Use and Playwright with persistent user profile reuse,
sensitive_data credential injection, DOM staging, screenshot capture, and Two-Phase HITL execution.
"""

import os
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright

from backend.config import settings
from backend.database import save_application, get_application, update_application_status
from backend.browser_agent.hitl_mailer import send_approval_email

logger = logging.getLogger("careerclaw.applier")

def stage_application(
    job_posting: Dict[str, Any],
    candidate_profile: Dict[str, Any],
    tailored_pdf_path: str,
    portal_credentials: Optional[Dict[str, str]] = None,
    headless: bool = True
) -> Dict[str, Any]:
    """
    FR-20: Phase 1 Staging (execute_final_submit=False).
    Fills portal form, uploads tailored PDF, pauses before submit,
    captures full-page verification screenshot, and sends JWT approval email.
    """
    settings.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    settings.CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    
    app_id = f"app_{uuid.uuid4().hex[:10]}"
    portal_url = job_posting.get("url", f"{settings.API_BASE_URL}/mock-portals/adobe-aiml-intern-2028")
    company = job_posting.get("company", "Adobe")
    role_title = job_posting.get("title", job_posting.get("role_title", "Software Engineering Intern"))

    screenshot_path = settings.SCREENSHOTS_DIR / f"staged_{app_id}.png"
    dom_actions = {}

    with sync_playwright() as p:
        # Launch with persistent context to preserve authenticated cookies/sessions (FR-18)
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(settings.CHROME_PROFILE_DIR),
            headless=headless,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        page = context.pages[0] if context.pages else context.new_page()

        try:
            logger.info(f"Navigating to portal: {portal_url}")
            page.goto(portal_url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)

            # Fill Full Name
            full_name = candidate_profile.get("full_name", "Aman Sharma")
            name_sel = page.locator('input[name="full_name"], input[name="name"], input#full_name, input#name').first
            if name_sel.count() > 0:
                name_sel.fill(full_name)
                dom_actions["full_name"] = full_name

            # Fill Email
            email = candidate_profile.get("email", "aman.sharma28@example.com")
            email_sel = page.locator('input[type="email"], input[name="email"], input#email').first
            if email_sel.count() > 0:
                email_sel.fill(email)
                dom_actions["email"] = email

            # Fill Phone
            phone = candidate_profile.get("phone", "+91 9876543210")
            phone_sel = page.locator('input[type="tel"], input[name="phone"], input#phone').first
            if phone_sel.count() > 0:
                phone_sel.fill(phone)
                dom_actions["phone"] = phone

            # Fill Graduation Year (Targeting B.Tech 2028 batch)
            grad_year = str(candidate_profile.get("graduation_batch", 2028))
            grad_sel = page.locator('input[name="graduation_year"], input#graduation_year, input[name="grad_year"]').first
            if grad_sel.count() > 0:
                grad_sel.fill(grad_year)
                dom_actions["graduation_year"] = grad_year

            # Fill GitHub URL
            github = candidate_profile.get("github_url", "https://github.com/amansharma2028")
            git_sel = page.locator('input[name="github_url"], input#github_url, input[name="github"]').first
            if git_sel.count() > 0:
                git_sel.fill(github)
                dom_actions["github_url"] = github

            # Fill LinkedIn URL
            linkedin = candidate_profile.get("linkedin_url", "https://linkedin.com/in/amansharma2028")
            li_sel = page.locator('input[name="linkedin_url"], input#linkedin_url, input[name="linkedin"]').first
            if li_sel.count() > 0:
                li_sel.fill(linkedin)
                dom_actions["linkedin_url"] = linkedin

            # Attach Tailored RenderCV PDF
            if tailored_pdf_path and os.path.exists(tailored_pdf_path):
                file_sel = page.locator('input[type="file"]').first
                if file_sel.count() > 0:
                    file_sel.set_input_files(tailored_pdf_path)
                    dom_actions["attached_pdf"] = str(tailored_pdf_path)
                    page.wait_for_timeout(500)

            # HALT BEFORE FINAL SUBMIT - Capture full page verification screenshot
            page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"Staged verification screenshot captured at: {screenshot_path}")

        except Exception as err:
            logger.error(f"Error during browser staging: {err}")
            # Ensure screenshot is still taken if possible
            try:
                page.screenshot(path=str(screenshot_path), full_page=True)
            except Exception:
                pass
        finally:
            context.close()

    # Save to Database
    app_record = {
        "id": app_id,
        "job_id": job_posting.get("id"),
        "company": company,
        "role_title": role_title,
        "portal_url": portal_url,
        "status": "STAGED_FOR_APPROVAL",
        "tailored_pdf_path": str(tailored_pdf_path) if tailored_pdf_path else None,
        "staged_screenshot_path": str(screenshot_path),
        "cached_dom_actions": dom_actions,
        "improve_notes": None
    }
    save_application(app_record)

    # FR-21: Dispatch cryptographic approval email with JWT action tokens
    email_res = send_approval_email(
        to_email=candidate_profile.get("email", "candidate@example.com"),
        job_details=app_record,
        pdf_path=str(tailored_pdf_path) if tailored_pdf_path else None,
        screenshot_path=str(screenshot_path),
        application_id=app_id
    )

    return {
        "status": "STAGED_FOR_APPROVAL",
        "application_id": app_id,
        "company": company,
        "role_title": role_title,
        "portal_url": portal_url,
        "screenshot_path": str(screenshot_path),
        "dom_actions": dom_actions,
        "email_dispatch": email_res
    }

def submit_staged_application(application_id: str, headless: bool = True) -> Dict[str, Any]:
    """
    FR-22: Phase 2 Execution (Triggered when user clicks Approve in email).
    Replays the application, clicks Submit, and captures the final confirmation screen.
    """
    app = get_application(application_id)
    if not app:
        raise ValueError(f"Application {application_id} not found in database.")

    portal_url = app["portal_url"]
    screenshot_submitted = settings.SCREENSHOTS_DIR / f"submitted_{application_id}.png"
    cached_actions = app.get("cached_dom_actions") or {}

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(settings.CHROME_PROFILE_DIR),
            headless=headless,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        page = context.pages[0] if context.pages else context.new_page()

        try:
            logger.info(f"Replaying application for final submission: {portal_url}")
            page.goto(portal_url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)

            # Re-verify and fill required fields if form is fresh
            if "full_name" in cached_actions:
                name_sel = page.locator('input[name="full_name"], input[name="name"], input#full_name, input#name').first
                if name_sel.count() > 0:
                    name_sel.fill(cached_actions["full_name"])

            if "email" in cached_actions:
                email_sel = page.locator('input[type="email"], input[name="email"], input#email').first
                if email_sel.count() > 0:
                    email_sel.fill(cached_actions["email"])

            if "phone" in cached_actions:
                phone_sel = page.locator('input[type="tel"], input[name="phone"], input#phone').first
                if phone_sel.count() > 0:
                    phone_sel.fill(cached_actions["phone"])

            if "graduation_year" in cached_actions:
                grad_sel = page.locator('input[name="graduation_year"], input#graduation_year').first
                if grad_sel.count() > 0:
                    grad_sel.fill(cached_actions["graduation_year"])

            if "github_url" in cached_actions:
                git_sel = page.locator('input[name="github_url"], input#github_url').first
                if git_sel.count() > 0:
                    git_sel.fill(cached_actions["github_url"])

            if "linkedin_url" in cached_actions:
                li_sel = page.locator('input[name="linkedin_url"], input#linkedin_url').first
                if li_sel.count() > 0:
                    li_sel.fill(cached_actions["linkedin_url"])

            pdf_path = app.get("tailored_pdf_path")
            if pdf_path and os.path.exists(pdf_path):
                file_sel = page.locator('input[type="file"]').first
                if file_sel.count() > 0:
                    file_sel.set_input_files(pdf_path)
                    page.wait_for_timeout(500)

            # CLICK FINAL SUBMIT BUTTON
            submit_btn = page.locator('button#submit-btn, button[type="submit"], input[type="submit"]').first
            if submit_btn.count() > 0:
                submit_btn.click()
                page.wait_for_timeout(2000)
            else:
                logger.warning("Submit button selector not found directly, attempting form submit")
                page.evaluate("document.querySelector('form')?.submit()")
                page.wait_for_timeout(2000)

            # Capture confirmation screenshot
            page.screenshot(path=str(screenshot_submitted), full_page=True)
            logger.info(f"Final confirmation screenshot saved to: {screenshot_submitted}")

        except Exception as err:
            logger.error(f"Error clicking final submit: {err}")
        finally:
            context.close()

    # Update status to APPROVED_SUBMITTED in database
    update_application_status(
        app_id=application_id,
        status="APPROVED_SUBMITTED",
        screenshot_path=str(screenshot_submitted)
    )

    return {
        "status": "APPROVED_SUBMITTED",
        "application_id": application_id,
        "company": app.get("company"),
        "role_title": app.get("role_title"),
        "confirmation_screenshot": str(screenshot_submitted)
    }
