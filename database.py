# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.settings import settings
from models.base import Base # This is now safe

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL or "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()