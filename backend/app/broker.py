# app/broker.py

from taskiq_pg.asyncpg import AsyncpgBroker

from .core.config import settings

broker = AsyncpgBroker(settings.DATABASE_URL)
