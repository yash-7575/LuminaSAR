"""LuminaSAR API - The Glass Box AI
SAR Narrative Generator with Explainable Audit Trail
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import health, sar
from app.routes import config_routes
from app.config import get_settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("luminasar")

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="LuminaSAR API",
    description="SAR Narrative Generator with Explainable Audit Trail — The Glass Box AI",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(sar.router, prefix="/api/v1/sar", tags=["SAR Generation"])
app.include_router(config_routes.router, prefix="/api/v1/config", tags=["Configuration"])


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 LuminaSAR API Starting...")
    logger.info(f"📡 Ollama: {settings.ollama_host} ({settings.ollama_model})")
    logger.info(f"🗄️ Supabase: {settings.supabase_url}")
    logger.info("✅ Ready to generate SARs!")


@app.get("/")
async def root():
    return {
        "name": "LuminaSAR API",
        "tagline": "Where Every Decision is Transparent",
        "version": settings.app_version,
        "docs": "/docs",
    }
