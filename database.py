"""
Database connection and session management.

Sets up SQLAlchemy engine and session factory for PostgreSQL.
Provides dependency injection for FastAPI routes.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from config import settings

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries if debug=True
    pool_size=5,          # Keep 5 connections in pool
    max_overflow=10,      # Allow 10 extra connections if needed
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for FastAPI routes.
    
    Provides a database session for each request.
    Automatically closes session after request completes.
    
    Usage in routes:
        @app.get("/sensors")
        def list_sensors(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
