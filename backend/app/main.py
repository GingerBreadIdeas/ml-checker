from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .api.api_v1.api import api_router
from .core.config import settings
from .db.database import Base, engine, get_db
from .db.init_db import init_db
from .kafka_producer import init_kafka_producer, close_kafka_producer

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mlechker API")

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
    init_kafka_producer()
    db = next(get_db())
    init_db(db)

from confluent_kafka import Producer

conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(conf)

def delivery_report(err, msg):
    if err is not None:
        print('Delivery failed:', err)
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

for i in range(10):
    producer.produce('test-topic', key=str(i), value=f'Message {i}', callback=delivery_report)
    producer.poll(0)

producer.flush()
