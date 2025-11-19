"""Notification model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text

from app.database import Base


class Notification(Base):
    """Notification database model."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    
    message = Column(Text, nullable=False)
    status = Column(String(50), default="sent")  # sent, failed
    error_message = Column(Text, nullable=True)
    
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Notification {self.id} for Match {self.match_id}>"

