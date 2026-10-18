import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.api.health import router as health_router
from backend.api.profile import router as profile_router
from backend.api.memory import router as memory_router
from backend.api.hunter import router as hunter_router
from backend.api.resumes import router as resumes_router
from backend.api.applications import router as applications_router
from backend.api.mock_portal import router as mock_portal_router
from backend.api.calendar import router as calendar_router
from backend.api.sandbox import router as sandbox_router
from backend.discovery.coordinator import start_discovery_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("careerorbit.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CareerOrbit database and services...")
    init_db()
    start_discovery_scheduler()
    yield
    logger.info("CareerOrbit backend shutting down.")

app = FastAPI(
    title="CareerOrbit API",
    description="Autonomous Student Opportunity Hunter, ATS Resume Compiler & HITL Browser Applier",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration supporting localhost and any Vercel domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health_router)
app.include_router(profile_router)
app.include_router(memory_router)
app.include_router(hunter_router)
app.include_router(resumes_router)
app.include_router(applications_router)
app.include_router(mock_portal_router)
app.include_router(calendar_router)
app.include_router(sandbox_router)

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    """Root status endpoint supporting GET and HEAD probes from cloud load balancers."""
    return {
        "app": "CareerOrbit",
        "description": "Nebius x NVIDIA Global AI Hackathon Autonomous Career Agent",
        "health_check": "/health",
        "operations_metrics": "/api/v1/operations/metrics",
        "docs": "/docs"
    }
