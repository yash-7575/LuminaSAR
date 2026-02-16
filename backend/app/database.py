"""Database connection using SQLAlchemy + Supabase PostgreSQL."""

import logging

logger = logging.getLogger("luminasar")

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

# Base class for models
Base = declarative_base()

from sqlalchemy.engine import URL

# Supabase DB Details (derived from settings.database_url or hardcoded for robustness)
db_url = settings.database_url
try:
    if "@" in db_url:
        # Reconstruct using URL.create to handle special characters correctly
        creds, host_part = db_url.rsplit("@", 1)
        scheme_user, password = creds.rsplit(":", 1)
        scheme, user = scheme_user.split("://")

        # Parse host and port
        host_port = host_part.split("/")[0]
        if ":" in host_port:
            host, port = host_port.split(":")
            port = int(port)
        else:
            host = host_port
            port = 5432

        database = host_part.split("/")[-1]

        url_object = URL.create(
            "postgresql",
            username=user,
            password=password,
            host=host,
            port=port,
            database=database,
        )
        logger.info(f"🗄️ Database Connecting to {host}:{port} as {user}")
    else:
        url_object = db_url
        logger.info(f"🗄️ Database Connecting via direct URL")
except Exception as e:
    logger.error(f"❌ Database URL Parsing Failed: {e}")
    url_object = db_url

# Final engine selection with SQLite fallback for robustness
try:
    # Try to connect once to verify Supabase
    temp_engine = create_engine(url_object, connect_args={"connect_timeout": 5})
    with temp_engine.connect() as conn:
        engine = temp_engine
        logger.info("✅ Connected to Supabase PostgreSQL")
except Exception as e:
    logger.warning(f"⚠️ Supabase connection failed ({e}). Falling back to local SQLite.")
    sqlite_url = "sqlite:///./luminasar.db"
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

    # Import models here to register them with Base.metadata
    from app.models.customer import Customer
    from app.models.transaction import Transaction
    from app.models.sar_case import SARCase
    from app.models.sar_narrative import SARNarrative
    from app.models.audit_trail import AuditTrail

    # Ensure tables are created in SQLite
    Base.metadata.create_all(bind=engine)
    logger.info("📁 Using local SQLite database (luminasar.db)")

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
