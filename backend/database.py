"""
AJEL Capital — Database Configuration
=======================================
Uses PostgreSQL in Docker, falls back to SQLite for local dev.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ajelcapital.db")

# PostgreSQL connection args differ from SQLite
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}
    logger.info("Using SQLite (local dev mode)")
else:
    logger.info(f"Using PostgreSQL: {DATABASE_URL.split('@')[0]}@***")

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency injection for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
