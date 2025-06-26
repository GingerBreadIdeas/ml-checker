from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..db.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    content = Column(Text, nullable=False)
    response = Column(Text, nullable=True)  # Optional response from chatbot
    is_prompt_injection = Column(Boolean, default=False)  # Flag for prompt injection attacks
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to user
    user = relationship("User", back_populates="messages")
    metrics = relationship("MessageMetrics", back_populates="message")

    metrics: Mapped[Optional["MessageMetrics"]] = relationship(
        back_populates="message",
        uselist=False,
    )

class MessageMetrics(Base):
    __tablename__ = "message_metrics"
    id = Column(Integer, primary_key=True, index=True)
    metrics_json = Column(JSONB)
    messag_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="SET NULL"),
        unique=True,
        nullable=True
    )
    message: Mapped[Optional[ChatMessage]] = relationship(back_populates="metrics")
