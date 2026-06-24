"""
Health Check API Endpoints
"""
import os
from fastapi import APIRouter

router = APIRouter(tags=["Health"])

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": ENVIRONMENT}
