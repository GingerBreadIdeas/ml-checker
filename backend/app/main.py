from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging

from .api.api_v1.api import api_router
from .core.config import settings
from .db.database import Base, engine, get_db
from .db.init_db import init_db
from .kafka_producer import init_kafka_producer, close_kafka_producer, get_kafka_producer

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
