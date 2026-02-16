"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal


SUPPORTED_JURISDICTIONS = ["IN", "US", "UK", "EU", "SG", "HK", "UAE", "AU"]


class Settings(BaseSettings):
    """LuminaSAR application settings."""

    # Supabase
    supabase_url: str = "https://ylsiaxywnegxtovqwyoh.supabase.co"
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""

    # JWT
    jwt_secret_key: str = "default_dev_secret_key_change_in_production"

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:latest"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"

    # Deployment & Jurisdiction
    deployment_env: str = "cloud"  # cloud, on-prem, hybrid
    jurisdiction: Literal["IN", "US", "UK", "EU", "SG", "HK", "UAE", "AU"] = "IN"

    # App
    app_name: str = "LuminaSAR"
    app_version: str = "1.0.0"
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Settings singleton (cache removed for debugging)."""
    from dotenv import load_dotenv

    load_dotenv(override=True)
    return Settings()
