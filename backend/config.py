import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

# Load .env from backend/.env or root .env
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_ROOT / ".env")

class Settings:
    # Nebius Token Factory & NVIDIA Models
    NEBIUS_API_KEY: str = os.getenv("NEBIUS_API_KEY", "")
    NEBIUS_BASE_URL: str = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1")
    
    # Tiered Nemotron 3 Models
    TIER1_MODEL: str = os.getenv("TIER1_MODEL", "nebius/nvidia/Nemotron-3_5-Lightning")
    TIER1_FALLBACK_MODEL: str = os.getenv("TIER1_FALLBACK_MODEL", "nebius/nvidia/Nemotron-3-Nano-30B-A3B")
    TIER2_MODEL: str = os.getenv("TIER2_MODEL", "nebius/nvidia/nemotron-3-super-120b-a12b")
    TIER3_MODEL: str = os.getenv("TIER3_MODEL", "nebius/nvidia/Nemotron-3-Ultra-550b-a55b")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nebius/Qwen/Qwen3-Embedding-8B")
    
    # Tavily Search API
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    
    # HITL Security & App URLs
    HITL_JWT_SECRET: str = os.getenv("HITL_JWT_SECRET", "careerclaw-secure-jwt-key-2026")
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:3000")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    # Storage and DB
    STORAGE_DIR: Path = Path(os.getenv("STORAGE_DIR", str(BACKEND_DIR / "storage")))
    SQLITE_DB_PATH: Path = Path(os.getenv("SQLITE_DB_PATH", str(BACKEND_DIR / "storage" / "careerclaw.db")))
    
    # Email / SMTP
    SMTP_EMAIL: str = os.getenv("SMTP_EMAIL", "")
    SMTP_APP_PASSWORD: str = os.getenv("SMTP_APP_PASSWORD", "")
    
    @property
    def is_nebius_configured(self) -> bool:
        return bool(self.NEBIUS_API_KEY and self.NEBIUS_API_KEY.strip() and self.NEBIUS_API_KEY != "your_key_here")

    @property
    def is_tavily_configured(self) -> bool:
        return bool(self.TAVILY_API_KEY and self.TAVILY_API_KEY.strip() and not self.TAVILY_API_KEY.startswith("tvly-your"))

settings = Settings()
# Ensure storage directory exists
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
