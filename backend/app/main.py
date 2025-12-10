import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .core.config import settings
from .database import Base, get_db
from .init_db import init_db
from .kafka_producer import (
    close_kafka_producer,
    get_kafka_producer,
    init_kafka_producer,
)
from .models import (
    ChatMessage,
    Project,
    ProjectToken,
    Prompt,
    Tag,
    User,
    UserRole,
)
from .routes import api_router

logger = logging.getLogger(__name__)

# Database tables are created via Alembic migrations

app = FastAPI(title="ML-Checker API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup SQLAdmin (only in non-test environments)
import os

if os.getenv("TEST_ENV", "false").lower() != "true":
    from .admin import setup_admin

    admin = setup_admin(app)

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
    # Skip initialization in test environments
    import os

    if os.getenv("TEST_ENV", "false").lower() == "true":
        logger.info("Skipping startup initialization (TEST_ENV=true)")
        return

    # Initialize Kafka producer with error handling
    try:
        init_kafka_producer()
        if get_kafka_producer() is not None:
            logger.info(
                "Kafka connection successful - prompt checks will be processed"
            )
        else:
            logger.warning(
                "Kafka connection failed - prompt checks will NOT be processed"
            )
    except Exception as e:
        logger.exception(f"Error initializing Kafka producer: {e}")

    # Initialize database
    db = next(get_db())
    init_db(db)
    logger.info("Database initialized successfully")
