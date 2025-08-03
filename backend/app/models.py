"""
SQLAlchemy models for the ML-Checker application.
"""
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, Enum, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import event
import enum

from .database import Base


# Association tables for many-to-many relationships with tags
user_tag_association = Table(
    'user_tags',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

chat_message_tag_association = Table(
    'chat_message_tags',
    Base.metadata,
    Column('chat_message_id', Integer, ForeignKey('chat_messages.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

prompt_tag_association = Table(
    'prompt_tags',
    Base.metadata,
    Column('prompt_id', Integer, ForeignKey('prompt_check.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

project_tag_association = Table(
    'project_tags',
    Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

# Removed session_tag_association - sessions are now just string properties


class RoleType(enum.Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False, default='default')
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="organization", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default='default')
    description = Column(Text, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    organization = relationship("Organization", back_populates="projects")
    prompts = relationship("Prompt", back_populates="project", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=project_tag_association, back_populates="projects")

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
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=user_tag_association, back_populates="users")


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    role = Column(Enum(RoleType), nullable=False, default=RoleType.MEMBER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_roles")
    organization = relationship("Organization", back_populates="user_roles")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=True)  # Simple string session identifier
    content = Column(Text, nullable=False)
    response = Column(Text, nullable=True)  # Optional response from chatbot
    is_prompt_injection = Column(Boolean, default=False)  # Flag for prompt injection attacks
    metrics = Column(JSONB)  # Direct JSONB column for metrics
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tags = relationship("Tag", secondary=chat_message_tag_association, back_populates="chat_messages")


class Prompt(Base):
    __tablename__ = "prompt_check"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    content = Column(JSONB)
    check_results = Column(JSONB, nullable=True)
    checked = Column(Boolean, default=False)

    # Relationships
    project = relationship("Project", back_populates="prompts")
    tags = relationship("Tag", secondary=prompt_tag_association, back_populates="prompts")

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
    projects = relationship("Project", secondary=project_tag_association, back_populates="tags")
    chat_messages = relationship("ChatMessage", secondary=chat_message_tag_association, back_populates="tags")
    prompts = relationship("Prompt", secondary=prompt_tag_association, back_populates="tags")


# Event listener to automatically create default organization and project when user is created
@event.listens_for(User, 'after_insert')
def create_default_org_and_project(mapper, connection, target):
    """
    Automatically create a default organization and project for new users
    """
    # Create default organization
    org_insert = Organization.__table__.insert().values(
        name='default',
        description=f'Default organization for {target.username}',
        is_active=True
    )
    result = connection.execute(org_insert)
    org_id = result.inserted_primary_key[0]
    
    # Create user role linking user to organization
    user_role_insert = UserRole.__table__.insert().values(
        user_id=target.id,
        organization_id=org_id,
        role=RoleType.ADMIN
    )
    connection.execute(user_role_insert)
    
    # Create default project in the organization
    project_insert = Project.__table__.insert().values(
        name='default',
        description='Default project',
        organization_id=org_id,
        is_default=True,
        is_active=True
    )
    connection.execute(project_insert)
