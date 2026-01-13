import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from taskiq.brokers.shared_broker import async_shared_broker

from .broker import broker
from .core.config import settings
from .database import get_db
from .init_db import init_db
from .routes import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
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

    try:
        yield
    finally:
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

if os.getenv("TEST_ENV", "false").lower() != "true":
    from .admin import setup_admin

    admin = setup_admin(app)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
