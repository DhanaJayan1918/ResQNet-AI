"""
ResQNet AI - Redis Connection Manager
Handles caching, pub/sub for WebSockets, rate limiting, and session management.
"""

import redis.asyncio as redis
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)


# ---- Mock Redis Client for Local Development Fallback ----

class MockRedis:
    def __init__(self, *args, **kwargs):
        self.db = {}
        
    async def ping(self):
        return True
        
    async def set(self, key, value, ex=None):
        self.db[key] = str(value)
        
    async def get(self, key):
        return self.db.get(key)
        
    async def delete(self, key):
        self.db.pop(key, None)
        
    async def exists(self, key):
        return int(key in self.db)
        
    async def flushdb(self):
        self.db.clear()
        
    async def close(self):
        pass
        
    def pipeline(self):
        return self
        
    async def incr(self, key):
        val = int(self.db.get(key, 0)) + 1
        self.db[key] = str(val)
        return val
        
    async def expire(self, key, seconds):
        pass
        
    async def execute(self):
        return []

    async def publish(self, channel, message):
        return 0


_redis_client: redis.Redis | MockRedis | None = None


async def connect_redis() -> None:
    """Initialize Redis connection."""
    global _redis_client
    settings = get_settings()

    logger.info(f"Connecting to Redis at {settings.REDIS_URL}...")
    try:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        # Verify connection
        await _redis_client.ping()
        logger.info("Connected to Redis successfully")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        logger.warning("⚠️  Falling back to in-memory Mock Redis for local development.")
        _redis_client = MockRedis()


def get_redis() -> redis.Redis | MockRedis:
    """Get the Redis client instance."""
    if _redis_client is None:
        raise RuntimeError("Redis is not connected. Call connect_redis() first.")
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        if hasattr(_redis_client, "close"):
            await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")



# ---- Helper Functions ----

async def cache_set(key: str, value: str, ttl_seconds: int = 300) -> None:
    """Set a cached value with TTL."""
    r = get_redis()
    await r.set(key, value, ex=ttl_seconds)


async def cache_get(key: str) -> str | None:
    """Get a cached value."""
    r = get_redis()
    return await r.get(key)


async def cache_delete(key: str) -> None:
    """Delete a cached key."""
    r = get_redis()
    await r.delete(key)


async def publish_event(channel: str, message: str) -> None:
    """Publish a message to a Redis pub/sub channel for WebSocket fanout."""
    r = get_redis()
    await r.publish(channel, message)


async def check_rate_limit(key: str, max_requests: int, window_seconds: int = 60) -> bool:
    """
    Simple sliding-window rate limiter.
    Returns True if request is allowed, False if rate limit exceeded.
    """
    r = get_redis()
    current = await r.get(key)
    if current and int(current) >= max_requests:
        return False
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, window_seconds)
    await pipe.execute()
    return True


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Add a JWT token ID to the blacklist."""
    r = get_redis()
    await r.set(f"token_blacklist:{jti}", "1", ex=ttl_seconds)


async def is_token_blacklisted(jti: str) -> bool:
    """Check if a JWT token is blacklisted."""
    r = get_redis()
    return await r.exists(f"token_blacklist:{jti}") > 0
