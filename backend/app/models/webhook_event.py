from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    webhook_id = Column(String, primary_key=True, nullable=False, unique=True)
    status = Column(String, nullable=False, index=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    payload = Column(Text, nullable=False)
