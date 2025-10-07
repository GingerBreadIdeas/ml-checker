"""
SQLAlchemy models for the ML-Checker application.
"""

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum,
    Table,
    JSON,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import event
import enum
import uuid

from .database import Base

# Use JSON everywhere, but swap in JSONB only when dialect is PostgreSQL
JSONPortable = JSON().with_variant(JSONB, "postgresql")


# Association tables for many-to-many relationships with tags
user_tag_association = Table(
    "user_tags",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

chat_message_tag_association = Table(
    "chat_message_tags",
    Base.metadata,
    Column(
        "chat_message_id", Integer, ForeignKey("chat_messages.id"), primary_key=True
    ),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

prompt_tag_association = Table(
    "prompt_tags",
    Base.metadata,
    Column("prompt_id", Integer, ForeignKey("prompt_check.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

project_tag_association = Table(
    "project_tags",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

# Removed session_tag_association - sessions are now just string properties


class RoleType(enum.Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="default")
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # Relationships
    prompts = relationship(
        "Prompt", back_populates="project", cascade="all, delete-orphan"
    )
    chat_messages = relationship(
        "ChatMessage", back_populates="project", cascade="all, delete-orphan"
    )
    user_roles = relationship(
        "UserRole", back_populates="project", cascade="all, delete-orphan"
    )
    tokens = relationship(
        "ProjectToken", back_populates="project", cascade="all, delete-orphan"
    )
    tags = relationship(
        "Tag", secondary=project_tag_association, back_populates="projects"
    )


class ProjectToken(Base):
    __tablename__ = "project_tokens"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="tokens")
    created_by = relationship("User", back_populates="created_tokens")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user_roles = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )
    created_tokens = relationship("ProjectToken", back_populates="created_by")
    tags = relationship("Tag", secondary=user_tag_association, back_populates="users")


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    role = Column(Enum(RoleType), nullable=False, default=RoleType.MEMBER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="user_roles")
    project = relationship("Project", back_populates="user_roles")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=True)  # Simple string session identifier
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    content = Column(Text, nullable=False)
    response = Column(Text, nullable=True)  # Optional response from chatbot
    is_prompt_injection = Column(
        Boolean, default=False
    )  # Flag for prompt injection attacks
    metrics = Column(JSONPortable)  # JSON column for metrics (JSONB on PostgreSQL)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="chat_messages")
    tags = relationship(
        "Tag", secondary=chat_message_tag_association, back_populates="chat_messages"
    )


class Prompt(Base):
    __tablename__ = "prompt_check"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    content = Column(JSONPortable)
    check_results = Column(JSONPortable, nullable=True)
    checked = Column(Boolean, default=False)

    # Relationships
    project = relationship("Project", back_populates="prompts")
    tags = relationship(
        "Tag", secondary=prompt_tag_association, back_populates="prompts"
    )


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String, nullable=True)  # Hex color for UI
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Many-to-many relationships
    users = relationship("User", secondary=user_tag_association, back_populates="tags")
    projects = relationship(
        "Project", secondary=project_tag_association, back_populates="tags"
    )
    chat_messages = relationship(
        "ChatMessage", secondary=chat_message_tag_association, back_populates="tags"
    )
    prompts = relationship(
        "Prompt", secondary=prompt_tag_association, back_populates="tags"
    )


# Event listener to automatically create default project when user is created
@event.listens_for(User, "after_insert")
def create_default_project(mapper, connection, target):
    """
    Automatically create a default project for new users
    """
    project_insert = Project.__table__.insert().values(
        name="default", description="Default project", is_default=True, is_active=True
    )

    result = connection.execute(project_insert)
    project_id = result.inserted_primary_key[0]

    user_role_insert = UserRole.__table__.insert().values(
        user_id=target.id, project_id=project_id, role=RoleType.ADMIN
    )
    connection.execute(user_role_insert)
