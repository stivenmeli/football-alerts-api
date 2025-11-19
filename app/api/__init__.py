"""API routes package."""

from fastapi import APIRouter

from app.api.routes import items, admin

api_router = APIRouter()

# Incluir routers de diferentes módulos
api_router.include_router(items.router, prefix="/items", tags=["Items"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])

