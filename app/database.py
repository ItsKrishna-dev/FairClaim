"""
Database configuration and session management
Handles SQLAlchemy setup and database connections
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment or use SQLite as default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fairclaim.db")

# Create SQLAlchemy engine
# For SQLite, we need check_same_thread=False to allow multiple threads
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,  # Set to True for SQL query debugging
    pool_pre_ping=True,  # Verify connections before using
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Base class for all ORM models
Base = declarative_base()


# Dependency function for FastAPI routes
def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI routes.
    Yields a database session and ensures it's closed after use.
    
    Usage in routes:
        def my_route(db: Session = Depends(get_db)):
            # Use db here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Function to initialize database tables
def init_db():
    """
    Create all database tables defined in models.
    Call this during application startup.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


# Function to drop all tables (use with caution!)
def drop_db():
    """
    Drop all database tables. Use only in development!
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped")
