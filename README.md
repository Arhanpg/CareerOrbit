# CareerClaw 🦅
### Autonomous Student Opportunity Hunter, Dynamic ATS Resume Compiler & HITL Browser Applier
**Engineered for the Nebius x NVIDIA Global AI Hackathon (Personal AI Track & Best Use of Tavily Bonus)**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![NVIDIA Nemotron 3](https://img.shields.io/badge/NVIDIA-Nemotron%203%20Models-76B900?logo=nvidia)](https://build.nvidia.com)
[![Nebius Token Factory](https://img.shields.io/badge/Nebius-Token%20Factory-00E5FF)](https://nebius.com)
[![Tavily Search API](https://img.shields.io/badge/Tavily-Live%20Search%20%26%20Extract-FF6B6B)](https://tavily.com)
[![Apple HIG Light Mode](https://img.shields.io/badge/Design-Apple%20HIG%20Light%20Mode-0071E3)](https://developer.apple.com/design/human-interface-guidelines)

---

## 🌟 Executive Summary

**CareerClaw** is a 24/7 autonomous career operating system designed to eliminate the high-friction internship and job application bottlenecks faced by undergraduate engineering students in India—specifically tailored for the **B.Tech 2028 graduating cohort**.

Rather than being a conversational chatbot wrapper, CareerClaw operates as an **always-on, credit-aware autonomous agent** powered by a **three-tier NVIDIA Nemotron 3 hierarchy** on **Nebius Token Factory**, hybrid vector-graph memory with Mem0 + Qdrant, deterministic typographical resume synthesis with RenderCV + Typst, sandboxed browser execution, and a cryptographic email approval gate.

```
                    ┌────────────────────────────────────────────────────────┐
                    │               Candidate Core Memory Vault               │
                    │         (Mem0 + Local Qdrant + CandidateMasterVault)   │
                    └───────────────────────────┬────────────────────────────┘
                                                │
                 ┌──────────────────────────────┼─────────────────────────────┐
                 │                              │                             │
                 ▼                              ▼                             ▼
   ┌───────────────────────────┐  ┌───────────────────────────┐  ┌───────────────────────────┐
   │ 24/7 Discovery Daemon     │  │ Dynamic ATS Resume Engine │  │ Browser Auto-Applier      │
   │ JobSpy + Tavily Search    │  │ Nemotron 3 Ultra 550B     │  │ Nemotron 3 Super 120B     │
   │ Naukri, LinkedIn, Unstop, │  │ RenderCV + Typst Engine   │  │ Browser-Use + CDP Session │
   │ Internshala & Big Tech    │  │ Hallucination-Free PDFs   │  │ Sandboxed Staging Flow    │
   └─────────────┬─────────────┘  └─────────────┬─────────────┘  └─────────────┬─────────────┘
                 │                              │                              │
                 └──────────────────────────────┼──────────────────────────────┘
                                                ▼
                                  ┌───────────────────────────┐
                                  │   FastAPI Control Plane   │
                                  │   Cryptographic JWT Gate  │
                                  │  [Approve] [Improve] [No] │
                                  └─────────────┬─────────────┘
                                                ▼
                                  ┌───────────────────────────┐
                                  │   Inbox & Calendar Sync   │
                                  │   Nemotron 3.5 Lightning  │
                                  │  Gmail OA Poller -> GCal  │
                                  └───────────────────────────┘
```

---

## ⚡ Tiered Model Routing on Nebius Token Factory

To maximize token credit longevity and minimize latency, all inference is deterministically routed across the **NVIDIA Nemotron 3** hierarchy via the OpenAI-compatible endpoint (`https://api.tokenfactory.nebius.com/v1`):

| Model Identifier on Nebius | Architecture & Context | Cost (In / Out per 1M) | Assigned Subsystem in CareerClaw |
| :--- | :--- | :--- | :--- |
| `nebius/Qwen/Qwen3-Embedding-8B` | 8B Dense Embedder (41K Context) | $0.01 / — | Vectorizing resumes, user memories, and project READMEs in Mem0 + Qdrant |
| `nebius/nvidia/Nemotron-3_5-Lightning` | 30B Hybrid MoE, 3B Active | $0.06 / $0.24 | **Tier 1 (High-Frequency Daemon)**: 24/7 B.Tech 2028 batch verification, scam filtering, Mem0 fact extraction, Gmail OA triage |
| `nebius/nvidia/nemotron-3-super-120b-a12b` | 120B Transformer-Mamba MoE | $0.30 / $0.90 | **Tier 2 (Browser & Form Navigation)**: Driving `browser-use` CDP loop, parsing DOM & accessibility trees, zero-leak credential injection |
| `nebius/nvidia/Nemotron-3-Ultra-550b-a55b` | 550B Frontier Reasoning MoE | $1.00 / $3.00 | **Tier 3 (Deep Synthesis)**: ATS keyword gap analysis, Action-Technology-Result bullet synthesis, Pydantic-validated RenderCV YAML generation |

---

## 🎨 Apple Human Interface Guidelines Design System

CareerClaw's frontend is built with Next.js App Router and strictly enforces the **Cupertino Light-Mode Aesthetic**:
- **App Canvas Background**: `#F5F5F7` (Apple System Grouped Canvas)
- **Elevated Card Surface**: `#FFFFFF` with `rounded-[20px]` and 1px hairline borders (`rgba(0,0,0,0.06)`)
- **Frosted Glass Navigation**: Translucent sticky bar with `backdrop-filter: blur(20px) saturate(180%)`
- **Typography**: Clean SF Pro / Inter typography with high contrast (`#1D1D1F` primary ink, `#86868B` secondary ink)
- **Primary Accent**: `#0071E3` Apple Blue pill buttons (`rounded-full`)
- **Semantic Badges**: High-contrast pills for 2028 batch match score, daemon status, and calendar events.

---

## 🏗️ 7-Stage End-to-End System Architecture

1. **Persistent Core Memory Vault**: Multi-resume upload (SDE vs. AI/ML) synthesized into canonical constraints (SQLite) and semantic facts (Mem0 + Qdrant).
2. **24/7 Discovery Daemon**: Asynchronous scraping across Naukri, LinkedIn, Indeed, Unstop, Internshala, and Big Tech portals (Google, Microsoft, Amazon, Adobe) using JobSpy + Tavily API.
3. **Nemotron Eligibility Gate**: Eliminates roles requiring 2+ YOE or older batches (2025/2026), filtering strictly for B.Tech 2028 students.
4. **Dynamic ATS Resume Engine**: Tailors RenderCV YAML and compiles ATS-friendly PDFs using Typst with zero hallucinations.
5. **Sandboxed Browser Auto-Applier**: Navigates portals with `browser-use`, pre-fills fields, attaches resume, and pauses before final submit.
6. **Cryptographic Email Approval Gate**: Dispatches HTML briefing emails with HMAC-SHA256 JWT action buttons ([Approve], [Improve], [Reject]).
7. **Inbox & Calendar Auto-Scheduler**: Monitors Gmail for Online Assessments (HackerRank/CodeSignal) and schedules focus blocks in Google Calendar in Asia/Kolkata (+05:30) time.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.11+ (Python 3.14 supported)
- Node.js 18+ (Node 24 supported)
- Nebius Token Factory API Key (`NEBIUS_API_KEY`)
- Tavily Search API Key (`TAVILY_API_KEY`)

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/Arhanpg/CareerOrbit.git
cd CareerOrbit

# Activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment variables
cp backend/.env.example backend/.env
# Edit backend/.env and paste your NEBIUS_API_KEY and TAVILY_API_KEY

# Run tests
pytest -v

# Start FastAPI server (runs on port 8000)
uvicorn backend.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000 in your browser
```

---

## 🧪 Automated Test Suite

Run the phase-by-phase test suite:
```bash
# Run all tests
pytest tests/ -v

# Run individual phase tests
pytest tests/test_phase1_foundation.py -v
```

---

## 📜 Hackathon Compliance & License

- **License**: [MIT License](LICENSE)
- **Primary Track**: Personal AI Track
- **Bonus Award Eligibility**: Best Use of Tavily ($3,000 Award)
- **Built For**: Nebius x NVIDIA Global AI Hackathon (October 2026)
