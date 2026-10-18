import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.api.health import router as health_router
from backend.api.profile import router as profile_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("careerclaw.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CareerClaw database and services...")
    init_db()
    yield
    logger.info("CareerClaw backend shutting down.")

app = FastAPI(
    title="CareerClaw API",
    description="Autonomous Student Opportunity Hunter, ATS Resume Compiler & HITL Browser Applier",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health_router)
app.include_router(profile_router)

@app.get("/")
def root():
    return {
        "app": "CareerClaw",
        "description": "Nebius x NVIDIA Global AI Hackathon Autonomous Career Agent",
        "health_check": "/health",
        "docs": "/docs"
    }
