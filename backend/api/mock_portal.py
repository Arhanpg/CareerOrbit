"""
CareerOrbit - FR-27 & Mock Corporate ATS Portal Route
Provides self-hosted, deterministic mock company ATS portals (e.g. Adobe Workday/Greenhouse style)
for 100% reproducible browser testing and 60-Second Judge Sandbox evaluation with zero external CAPTCHAs.
"""

from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from typing import Optional

router = APIRouter(prefix="/mock-portals", tags=["Judge Mock Portals"])

MOCK_PORTAL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Adobe Careers | AI/ML Software Engineering Intern (2028)</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: #F8F9FA;
      margin: 0;
      padding: 40px 20px;
      color: #2D3748;
    }
    .container {
      max-width: 680px;
      margin: 0 auto;
      background: #FFFFFF;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.06);
      padding: 40px;
      border: 1px solid #E2E8F0;
    }
    .header {
      border-bottom: 2px solid #EDF2F7;
      padding-bottom: 20px;
      margin-bottom: 24px;
    }
    .logo {
      color: #EB1000;
      font-weight: 800;
      font-size: 24px;
      letter-spacing: -0.03em;
    }
    h1 {
      font-size: 22px;
      margin: 12px 0 6px 0;
      color: #1A202C;
    }
    .meta {
      font-size: 13px;
      color: #718096;
      margin-bottom: 8px;
    }
    .form-group {
      margin-bottom: 18px;
    }
    label {
      display: block;
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 6px;
      color: #4A5568;
    }
    input[type="text"], input[type="email"], input[type="number"], select {
      width: 100%;
      padding: 10px 14px;
      border: 1px solid #CBD5E0;
      border-radius: 6px;
      font-size: 14px;
      box-sizing: border-box;
      transition: border-color 0.2s;
    }
    input:focus {
      outline: none;
      border-color: #3182CE;
    }
    .file-input {
      padding: 10px;
      background: #F7FAFC;
      border: 1px dashed #CBD5E0;
      border-radius: 6px;
      width: 100%;
      box-sizing: border-box;
    }
    .btn-submit {
      background-color: #EB1000;
      color: white;
      border: none;
      padding: 14px 28px;
      font-size: 15px;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      width: 100%;
      margin-top: 12px;
    }
    .btn-submit:hover {
      background-color: #C50C00;
    }
    .badge {
      display: inline-block;
      background: #EBF8FF;
      color: #2B6CB0;
      font-size: 12px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 9999px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="logo">Adobe</div>
      <h1>AI/ML Software Engineering Intern (2028 Cohort)</h1>
      <div class="meta">Bangalore / Noida, India &bull; Requisition ID: ADB-2028-AIML &bull; <span class="badge">Open Application</span></div>
    </div>

    <form id="application-form" action="/mock-portals/adobe-aiml-intern-2028/submit" method="POST" enctype="multipart/form-data">
      <div class="form-group">
        <label for="full_name">Candidate Full Name *</label>
        <input type="text" id="full_name" name="full_name" placeholder="e.g. Aman Sharma" required>
      </div>

      <div class="form-group">
        <label for="email">Email Address *</label>
        <input type="email" id="email" name="email" placeholder="e.g. aman.sharma@example.com" required>
      </div>

      <div class="form-group">
        <label for="phone">Phone Number (+E.164) *</label>
        <input type="text" id="phone" name="phone" placeholder="+91 9876543210" required>
      </div>

      <div class="form-group">
        <label for="graduation_year">Graduation Year (Cohort Batch) *</label>
        <input type="number" id="graduation_year" name="graduation_year" value="2028" min="2027" max="2029" required>
      </div>

      <div class="form-group">
        <label for="github_url">GitHub Profile URL *</label>
        <input type="text" id="github_url" name="github_url" placeholder="https://github.com/..." required>
      </div>

      <div class="form-group">
        <label for="linkedin_url">LinkedIn Profile URL</label>
        <input type="text" id="linkedin_url" name="linkedin_url" placeholder="https://linkedin.com/in/...">
      </div>

      <div class="form-group">
        <label for="resume_file">Attach Tailored ATS Resume (PDF) *</label>
        <input type="file" id="resume_file" name="resume_file" class="file-input" accept=".pdf">
      </div>

      <button type="submit" id="submit-btn" class="btn-submit">Submit Application</button>
    </form>
  </div>
</body>
</html>
"""

CONFIRMATION_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Application Received | Adobe Careers</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: #F8F9FA;
      margin: 0;
      padding: 60px 20px;
      color: #2D3748;
      text-align: center;
    }
    .card {
      max-width: 560px;
      margin: 0 auto;
      background: white;
      border-radius: 16px;
      padding: 48px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.06);
      border: 1px solid #E2E8F0;
    }
    .icon {
      font-size: 48px;
      color: #38A169;
      margin-bottom: 16px;
    }
    h1 {
      font-size: 24px;
      color: #1A202C;
      margin-bottom: 8px;
    }
    p {
      color: #4A5568;
      line-height: 1.6;
    }
    .code {
      background: #EDF2F7;
      padding: 8px 16px;
      border-radius: 6px;
      font-family: monospace;
      font-weight: 700;
      color: #2B6CB0;
      display: inline-block;
      margin: 16px 0;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">&#10004;</div>
    <h1 id="confirmation-heading">Application Submitted Successfully!</h1>
    <p>Thank you for applying to the <strong>AI/ML Software Engineering Intern (2028 Cohort)</strong> position at Adobe India.</p>
    <div>Confirmation ID: <span class="code" id="confirmation-id">ADB-2028-9842</span></div>
    <p style="font-size:13px; color:#718096;">Our University Talent Acquisition team will review your application and send HackerRank assessment instructions to your registered email.</p>
  </div>
</body>
</html>
"""

@router.get("/adobe-aiml-intern-2028", response_class=HTMLResponse)
@router.get("/adobe-intern", response_class=HTMLResponse)
def render_adobe_mock_portal():
    return MOCK_PORTAL_HTML

@router.post("/adobe-aiml-intern-2028/submit", response_class=HTMLResponse)
@router.post("/adobe-intern/submit", response_class=HTMLResponse)
async def handle_mock_submit(
    full_name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    graduation_year: int = Form(2028),
    github_url: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    resume_file: Optional[UploadFile] = File(None)
):
    return CONFIRMATION_HTML
