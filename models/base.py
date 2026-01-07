# models/base.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """The central point for all model inheritance."""
    pass