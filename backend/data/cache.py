"""
AJEL Capital — Redis Cache Helper
Security: Redis is on the internal Docker network, not exposed to internet.
"""
import redis
import json
import os
import logging

logger = logging.getLogger(__name__)

_redis_client = None

def get_redis() -> redis.Redis:
    """Get or create Redis client (singleton). Falls back gracefully if unavailable."""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
    return _redis_client


def cache_get(key: str):
    """Get value from Redis cache, returns None on miss or error."""
    try:
        r = get_redis()
        val = r.get(key)
        if val is None:
            return None
        return json.loads(val)
    except Exception as e:
        logger.warning(f"Redis GET failed for {key}: {e}")
        return None


def cache_set(key: str, value, ttl_seconds: int = 60):
    """Set value in Redis cache with TTL. Silently fails if Redis is unavailable."""
    try:
        r = get_redis()
        r.setex(key, ttl_seconds, json.dumps(value))
        return True
    except Exception as e:
        logger.warning(f"Redis SET failed for {key}: {e}")
        return False


def cache_delete(key: str):
    """Delete a key from Redis."""
    try:
        r = get_redis()
        r.delete(key)
    except Exception as e:
        logger.warning(f"Redis DEL failed for {key}: {e}")
