"""Health check endpoint."""

from fastapi import APIRouter
from app.schemas.response import HealthResponse
from app.config import get_settings
import httpx

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check the health of all services."""

    # Check Ollama
    ollama_connected = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_host}/api/tags")
            ollama_connected = resp.status_code == 200
    except Exception:
        pass

    # Check database
    db_connected = False
    try:
        from app.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_connected = True
    except Exception as e:
        print(f"DEBUG DB HEALTH ERROR: {e}")
        pass

    return HealthResponse(
        status="healthy" if (ollama_connected and db_connected) else "degraded",
        version=settings.app_version,
        ollama_connected=ollama_connected,
        database_connected=db_connected,
    )
