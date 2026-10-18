import os
import sqlite3
import logging
from pathlib import Path
from typing import Optional, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from .config import settings

logger = logging.getLogger("NU_DATABASE_CORE")

Base = declarative_base()

# SQLAlchemy Engine Initialization (Environment-driven)
db_url = settings.DATABASE_URL
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # Ensure directory exists for sqlite
    db_path_str = db_url.replace("sqlite:///", "")
    if db_path_str:
        Path(db_path_str).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(db_url, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_connection() -> sqlite3.Connection:
    """Returns a raw SQLite connection to the primary database."""
    db_path = settings.DATA_DIR / "nu_tokens.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def get_db_session() -> Generator[Session, None, None]:
    """Dependency for obtaining a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def init_core_database():
    """Initializes SQLAlchemy tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Core database tables initialized successfully via SQLAlchemy.")
    except Exception as e:
        logger.error(f"Error initializing core database: {e}", exc_info=True)
