# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.settings import settings
from models.base import Base # This is now safe

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL or "sqlite:///./test.db"

# Optimize connection pooling for faster startup and better performance
# For PostgreSQL (Render), use connection pooling
if "postgresql" in SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=5,  # Number of connections to maintain
        max_overflow=10,  # Additional connections beyond pool_size
        pool_pre_ping=True,  # Verify connections before using (important for Render)
        pool_recycle=300,  # Recycle connections after 5 minutes
        connect_args={"connect_timeout": 5}  # Fast connection timeout
    )
else:
    # SQLite configuration (for local dev)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()