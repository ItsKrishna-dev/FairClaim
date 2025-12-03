from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database (no installation needed!)
SQLALCHEMY_DATABASE_URL = "sqlite:///./fairclaim.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
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

