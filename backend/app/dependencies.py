"""
ResQNet AI - Dependency Injection
Provides shared dependencies for route handlers.
"""

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.mongodb import get_database
from app.db.redis_client import get_redis


async def get_db() -> AsyncIOMotorDatabase:
    """Dependency that provides the MongoDB database instance."""
    return get_database()


async def get_cache():
    """Dependency that provides the Redis client instance."""
    return get_redis()
