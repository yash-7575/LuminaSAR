"""Configuration endpoint — Exposes deployment and jurisdiction settings."""

from fastapi import APIRouter
from app.config import get_settings, SUPPORTED_JURISDICTIONS
from app.schemas.response import ConfigResponse

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=ConfigResponse)
async def get_config():
    """Return current deployment configuration and supported jurisdictions."""
    return ConfigResponse(
        jurisdiction=settings.jurisdiction,
        deployment_env=settings.deployment_env,
        supported_jurisdictions=SUPPORTED_JURISDICTIONS,
    )
