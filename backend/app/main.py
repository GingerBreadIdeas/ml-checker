import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from taskiq.brokers.shared_broker import async_shared_broker

from .broker import broker
from .core.config import settings
from .database import Base, get_db
from .init_db import init_db
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
from .tasks import flush_message_queue

logger = logging.getLogger(__name__)


# Periodic task to flush message queue
async def periodic_queue_flush():
    """Periodically flush the message queue to ensure batches are processed"""
    flush_interval = float(os.getenv("METRICS_BATCH_TIMEOUT", "5.0"))
    while True:
        try:
            await asyncio.sleep(flush_interval)
            await flush_message_queue.kiq()
            logger.debug("Triggered periodic queue flush")
        except Exception as e:
            logger.error(f"Error in periodic queue flush: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Skip broker startup in test environment
    if os.getenv("TEST_ENV", "false").lower() != "true":
        await broker.startup()
        async_shared_broker.default_broker(broker)

    # Initialize database
    if os.getenv("TEST_ENV", "false").lower() != "true":
        db = next(get_db())
        try:
            init_db(db)
            logger.info("Database initialized successfully")
        finally:
            db.close()

    # Start periodic queue flush task
    flush_task = asyncio.create_task(periodic_queue_flush())
    logger.info("Started periodic message queue flush task")

    try:
        yield
    finally:
        if os.getenv("TEST_ENV", "false").lower() != "true":
            await broker.shutdown()
        # Cancel the flush task
        flush_task.cancel()
        try:
            await flush_task
        except asyncio.CancelledError:
            pass
        await broker.shutdown()


app = FastAPI(title="ML-Checker API", lifespan=lifespan)
app.state.taskiq_broker_started = False

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
