#!/usr/bin/env python
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..database import Base


class Prompt(Base):
    __tablename__ = "prompt_check"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    # content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    content = Column(JSONB)
    check_results = Column(JSONB, nullable=True)
    checked = Column(Boolean, default=False)

    # Relationship to user
    user = relationship("User", back_populates="prompts")