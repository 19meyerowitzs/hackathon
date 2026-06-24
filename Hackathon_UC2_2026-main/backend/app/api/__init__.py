"""
API Routers Package
"""
from fastapi import APIRouter

# Import all routers
from .health import router as health_router
from .ui import router as ui_router
from .reputation import router as reputation_router

# Export routers
__all__ = ["health_router", "ui_router", "reputation_router"]
