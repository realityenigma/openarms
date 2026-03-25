"""Health check and info endpoints"""
from fastapi import APIRouter
from armswideopen.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@router.get("/info")
def info():
    """API info endpoint"""
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "api_version": settings.api_version,
    }
