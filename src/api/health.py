"""Public service health endpoints."""

from fastapi import APIRouter

from src.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/")
def index() -> dict[str, str]:
    return {"name": get_settings().app.name, "status": "running"}


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}
