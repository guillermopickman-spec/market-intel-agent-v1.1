from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .base import Base

class MissionLog(Base):
    __tablename__ = "mission_logs"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, index=True)
    query = Column(String(255))
    response = Column(Text)
    status = Column(String(50)) # e.g., 'COMPLETED', 'FAILED'
    created_at = Column(DateTime, default=datetime.utcnow)