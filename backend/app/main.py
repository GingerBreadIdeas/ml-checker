from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging

from sqladmin import Admin, ModelView

from .routes import api_router
from .core.config import settings
from .database import Base, engine, get_db
from .init_db import init_db
from .kafka_producer import init_kafka_producer, close_kafka_producer, get_kafka_producer
from .models import User, Organization, Project, UserRole, ChatMessage, Prompt, Tag

logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ML-Checker API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup SQLAdmin
admin = Admin(app, engine)

# Admin model views
class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.email, User.is_active, User.is_superuser, User.created_at]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.username, User.email, User.created_at]

class OrganizationAdmin(ModelView, model=Organization):
    column_list = [Organization.id, Organization.name, Organization.description, Organization.is_active, Organization.created_at]
    column_searchable_list = [Organization.name]

class ProjectAdmin(ModelView, model=Project):
    column_list = [Project.id, Project.name, Project.organization_id, Project.is_default, Project.is_active, Project.created_at]
    column_searchable_list = [Project.name]

class UserRoleAdmin(ModelView, model=UserRole):
    column_list = [UserRole.id, UserRole.user_id, UserRole.organization_id, UserRole.role, UserRole.created_at]

class ChatMessageAdmin(ModelView, model=ChatMessage):
    column_list = [ChatMessage.id, ChatMessage.content, ChatMessage.session_id, ChatMessage.is_prompt_injection, ChatMessage.created_at]
    column_searchable_list = [ChatMessage.content]
    column_sortable_list = [ChatMessage.id, ChatMessage.created_at]

class PromptAdmin(ModelView, model=Prompt):
    column_list = [Prompt.id, Prompt.project_id, Prompt.checked, Prompt.created_at]

class TagAdmin(ModelView, model=Tag):
    column_list = [Tag.id, Tag.name, Tag.description, Tag.color, Tag.is_active, Tag.created_at]
    column_searchable_list = [Tag.name]

# Add admin views
admin.add_view(UserAdmin)
admin.add_view(OrganizationAdmin)
admin.add_view(ProjectAdmin)
admin.add_view(UserRoleAdmin)
# Removed SessionAdmin - sessions are now just string properties
admin.add_view(ChatMessageAdmin)
admin.add_view(PromptAdmin)
admin.add_view(TagAdmin)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("shutdown")
def shutdown_event():
    close_kafka_producer()

# Initialize database with test data
@app.on_event("startup")
async def startup_event():
    # Initialize Kafka producer with error handling
    try:
        init_kafka_producer()
        if get_kafka_producer() is not None:
            logger.info("Kafka connection successful - prompt checks will be processed")
        else:
            logger.warning("Kafka connection failed - prompt checks will NOT be processed")
    except Exception as e:
        logger.exception(f"Error initializing Kafka producer: {e}")
        
    # Initialize database
    db = next(get_db())
    init_db(db)
    logger.info("Database initialized successfully")
