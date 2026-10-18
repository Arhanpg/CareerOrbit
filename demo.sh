#!/bin/bash
# CareerOrbit One-Command Startup Script for Judges and Hackathon Reviewers

echo "================================================================="
echo "  Starting CareerOrbit Autonomous Career Operating System"
echo "  Nebius x NVIDIA Global AI Hackathon (Personal AI Track)"
echo "================================================================="

# 1. Start FastAPI Backend on port 8000
echo "[1/2] Starting FastAPI backend on http://localhost:8000..."
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# 2. Start Next.js Frontend on port 3000
echo "[2/2] Starting Next.js Cupertino Light frontend on http://localhost:3000..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo "================================================================="
echo "  CareerOrbit Control Plane is live!"
echo "  Web UI:    http://localhost:3000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  Judge 60s: Toggle 'Judge 60s Demo: ON' in top navigation bar"
echo "================================================================="

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
