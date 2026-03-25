"""API routes module"""
from fastapi import APIRouter
from armswideopen.api import datasets, models, users

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(models.router)
api_router.include_router(datasets.router)

__all__ = ["api_router"]
