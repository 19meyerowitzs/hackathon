"""
FastAPI Main Application for Reputation Intelligence.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

from .database import init_db
from .api import health_router, ui_router, reputation_router, web_search_router

load_dotenv()

# Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
environment = os.getenv("Environment", "dev")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://localhost:3000").split(",")

# Read token — same pattern as reference app
_key_dev = os.getenv("X_API_KEY", "").strip()
_key_prod = os.getenv("X_API_KEY_Prod", "").strip()
default_token = _key_dev if 'dev' in environment.lower() else _key_prod

# Set OPENAI_API_KEY so LiteLLM proxy client always initializes
if default_token:
    os.environ.setdefault("OPENAI_API_KEY", default_token)

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Reputation Intelligence API",
    description="AI-powered press clipping analysis platform with competitive intelligence",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ═══════════════════════════════════════════════════════════════
# INCLUDE API ROUTERS
# ═══════════════════════════════════════════════════════════════

app.include_router(ui_router)
app.include_router(health_router)
app.include_router(reputation_router)
app.include_router(web_search_router)

# ═══════════════════════════════════════════════════════════════


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
